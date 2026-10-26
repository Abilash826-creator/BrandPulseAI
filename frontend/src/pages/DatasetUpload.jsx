import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBrand } from '../context/BrandContext';
import { datasetAPI } from '../services/api';
import { useSampleDatasets } from '../hooks/useSampleDatasets';
import DatasetDropzone from '../components/dataset/DatasetDropzone';
import PastedReviewsCard from '../components/dataset/PastedReviewsCard';
import IngestionConfigCard from '../components/dataset/IngestionConfigCard';
import SampleDatasetsPanel from '../components/dataset/SampleDatasetsPanel';
import IngestionProgressModal from '../components/dataset/IngestionProgressModal';
import { UploadCloud, Sparkles, ChevronRight, FileText } from 'lucide-react';

const DatasetUpload = () => {
  const navigate = useNavigate();
  const { brands, activeBrand, setActiveBrand, refreshBrands } = useBrand();

  const fileInputRef = useRef(null);
  const [uploadTab, setUploadTab] = useState('file'); // 'file' or 'paste'
  const [pastedText, setPastedText] = useState('');
  const [pastedSource, setPastedSource] = useState('WhatsApp Feedback');
  const [pastedRating, setPastedRating] = useState('5');
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewData, setPreviewData] = useState(null);

  // Configuration Form State
  const [targetBrandMode, setTargetBrandMode] = useState('active'); // 'active', 'new', 'existing'
  const [selectedBrandId, setSelectedBrandId] = useState(activeBrand?.id || '');
  const [newBrandName, setNewBrandName] = useState('');
  const [productNameInput, setProductNameInput] = useState('');
  const [autoDetectProduct, setAutoDetectProduct] = useState(true);
  const [ingestionMode, setIngestionMode] = useState('append'); // 'append' or 'replace'
  const [generateSummary, setGenerateSummary] = useState(true);

  // Samples State from React Query
  const { data: samples = [], isLoading: samplesLoading } = useSampleDatasets();
  const [processingSampleId, setProcessingSampleId] = useState(null);

  // Processing & Pipeline Progress
  const [processing, setProcessing] = useState(false);
  const [pipelineStep, setPipelineStep] = useState(0); // 0 to 5
  const [ingestResult, setIngestResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (activeBrand && !selectedBrandId) {
      setSelectedBrandId(activeBrand.id);
    }
  }, [activeBrand]);

  // Handle Drag & Drop
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  };

  const handleFileSelected = async (file) => {
    setSelectedFile(file);
    setErrorMessage('');
    setPreviewLoading(true);
    setPreviewData(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await datasetAPI.previewFile(formData);
      setPreviewData(res.data);
      if (res.data.detected_brand && targetBrandMode === 'new' && !newBrandName) {
        setNewBrandName(res.data.detected_brand);
      }
      if (res.data.detected_product && !productNameInput) {
        setProductNameInput(res.data.detected_product);
      }
    } catch (err) {
      console.error("Preview failed:", err);
      setErrorMessage(err.response?.data?.detail || "Could not preview file structure. Upload may still succeed.");
    } finally {
      setPreviewLoading(false);
    }
  };

  const runPipelineAnimation = async () => {
    for (let i = 1; i <= 5; i++) {
      setPipelineStep(i);
      await new Promise(r => setTimeout(r, 450));
    }
  };

  const handleUploadAndProcess = async () => {
    if (!selectedFile) return;

    setProcessing(true);
    setErrorMessage('');
    setIngestResult(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    let finalBrandId = null;
    let finalBrandName = null;

    if (targetBrandMode === 'active') {
      finalBrandId = activeBrand?.id;
      finalBrandName = activeBrand?.name;
    } else if (targetBrandMode === 'existing') {
      finalBrandId = selectedBrandId;
      const found = brands.find(b => b.id === selectedBrandId);
      finalBrandName = found ? found.name : null;
    } else if (targetBrandMode === 'new') {
      finalBrandName = newBrandName.trim() || 'Custom Uploaded Brand';
    }

    if (finalBrandId) formData.append('brand_id', finalBrandId);
    if (finalBrandName) formData.append('brand_name', finalBrandName);
    if (productNameInput.trim()) formData.append('product_name', productNameInput.trim());
    formData.append('auto_detect_product', autoDetectProduct ? 'true' : 'false');
    formData.append('ingestion_mode', ingestionMode);
    formData.append('generate_summary', generateSummary ? 'true' : 'false');

    try {
      const pipelinePromise = runPipelineAnimation();
      const apiPromise = datasetAPI.uploadAndIngest(formData);

      const [_, response] = await Promise.all([pipelinePromise, apiPromise]);
      setIngestResult(response.data);

      const brandId = response.data.brand_id;
      const updatedList = await refreshBrands(brandId);
      if (brandId && updatedList?.length) {
        const found = updatedList.find(b => b.id === brandId);
        if (found) setActiveBrand(found);
      }

      setTimeout(() => {
        navigate('/', { 
          state: { 
            justIngested: true, 
            brandName: response.data.brand_name,
            productName: response.data.primary_product,
            count: response.data.total_records_processed,
            nss: response.data.net_sentiment_score
          } 
        });
      }, 1400);

    } catch (err) {
      console.error("Ingestion failed:", err);
      setErrorMessage(err.response?.data?.detail || "Dataset ingestion failed. Please try again.");
    } finally {
      setProcessing(false);
      setPipelineStep(0);
    }
  };

  const handleIngestSample = async (sample) => {
    setProcessingSampleId(sample.id);
    setProcessing(true);
    setErrorMessage('');
    setIngestResult(null);

    try {
      await runPipelineAnimation();
      const targetBrand = activeBrand?.id || null;
      const res = await datasetAPI.ingestSample(sample.id, targetBrand, ingestionMode);
      setIngestResult(res.data);
      
      const brandId = res.data.brand_id;
      const updatedList = await refreshBrands(brandId);
      if (brandId && updatedList?.length) {
        const found = updatedList.find(b => b.id === brandId);
        if (found) setActiveBrand(found);
      }

      setTimeout(() => {
        navigate('/', { 
          state: { 
            justIngested: true, 
            brandName: res.data.brand_name,
            productName: res.data.primary_product,
            count: res.data.total_records_processed,
            nss: res.data.net_sentiment_score
          } 
        });
      }, 1400);

    } catch (err) {
      console.error("Sample ingestion error:", err);
      setErrorMessage(err.response?.data?.detail || "Failed to ingest sample dataset.");
    } finally {
      setProcessing(false);
      setProcessingSampleId(null);
      setPipelineStep(0);
    }
  };

  const handlePasteReviews = async () => {
    if (!pastedText.trim() || !activeBrand) return;
    setProcessing(true);
    setErrorMessage('');
    try {
      await runPipelineAnimation();
      const res = await datasetAPI.pasteReviews({
        text: pastedText,
        brand_id: activeBrand.id,
        source: pastedSource,
        default_rating: parseInt(pastedRating, 10),
        mode: ingestionMode
      });
      setIngestResult(res.data);
      setTimeout(() => {
        navigate('/', {
          state: {
            justIngested: true,
            brandName: activeBrand.name,
            count: res.data?.total_reviews_parsed || 1
          }
        });
      }, 1400);
    } catch (err) {
      console.error('Failed to paste reviews:', err);
      setErrorMessage(err.response?.data?.detail || 'Failed to parse pasted feedback.');
    } finally {
      setProcessing(false);
      setPipelineStep(0);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in max-w-6xl">
      {/* Top Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl lg:text-2xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2.5">
              <UploadCloud className="w-6 h-6 text-[#2563EB]" />
              <span>Upload Data & Customer Reviews</span>
            </h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-[#2563EB] border border-blue-200 flex items-center space-x-1">
              <Sparkles className="w-3 h-3" />
              <span>PDF • CSV • JSON</span>
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Upload customer reviews, survey PDFs, or spreadsheets to automatically analyze customer mood, topics, and satisfaction.
          </p>
        </div>

        <div className="flex items-center space-x-2.5 flex-wrap gap-2">
          <a
            href="/sample_customer_reviews.pdf"
            download="sample_customer_reviews.pdf"
            className="px-3.5 py-2.5 rounded-xl bg-purple-50 hover:bg-purple-100 text-purple-700 font-bold text-xs transition flex items-center space-x-1.5 border border-purple-200 shadow-2xs"
            title="Download ready-to-use sample reviews PDF"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Download Sample PDF</span>
          </a>

          <button
            onClick={() => navigate('/')}
            className="px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition flex items-center space-x-2 border border-slate-200"
          >
            <span>View Dashboard</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Quick-Start Pre-packaged Dataset Cards */}
      {samples && samples.length > 0 && (
        <SampleDatasetsPanel
          samples={samples}
          samplesLoading={samplesLoading}
          processing={processing}
          processingSampleId={processingSampleId}
          handleIngestSample={handleIngestSample}
        />
      )}

      {/* Main Grid: Upload Dropzone & Configuration Form */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Dropzone or Paste Box (7 Cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Tab Selector */}
          <div className="flex items-center space-x-2 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
            <button
              type="button"
              onClick={() => setUploadTab('file')}
              className={`flex-1 py-2 rounded-lg flex items-center justify-center space-x-1.5 transition ${
                uploadTab === 'file' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <UploadCloud className="w-4 h-4 text-blue-600" />
              <span>Upload File (CSV, Excel, PDF)</span>
            </button>
            <button
              type="button"
              onClick={() => setUploadTab('paste')}
              className={`flex-1 py-2 rounded-lg flex items-center justify-center space-x-1.5 transition ${
                uploadTab === 'paste' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <FileText className="w-4 h-4 text-emerald-600" />
              <span>Paste Reviews / Screenshot Text</span>
            </button>
          </div>

          {uploadTab === 'file' ? (
            <DatasetDropzone
              fileInputRef={fileInputRef}
              dragActive={dragActive}
              handleDrag={handleDrag}
              handleDrop={handleDrop}
              handleFileInputChange={handleFileInputChange}
              selectedFile={selectedFile}
              errorMessage={errorMessage}
              previewLoading={previewLoading}
              previewData={previewData}
            />
          ) : (
            <PastedReviewsCard
              pastedSource={pastedSource}
              setPastedSource={setPastedSource}
              pastedRating={pastedRating}
              setPastedRating={setPastedRating}
              pastedText={pastedText}
              setPastedText={setPastedText}
              errorMessage={errorMessage}
              processing={processing}
              handlePasteReviews={handlePasteReviews}
            />
          )}
        </div>

        {/* Right Column: AI Ingestion Controls & Settings (5 Cols) */}
        <div className="lg:col-span-5 space-y-4">
          <IngestionConfigCard
            brands={brands}
            targetBrandMode={targetBrandMode}
            setTargetBrandMode={setTargetBrandMode}
            selectedBrandId={selectedBrandId}
            setSelectedBrandId={setSelectedBrandId}
            newBrandName={newBrandName}
            setNewBrandName={setNewBrandName}
            productNameInput={productNameInput}
            setProductNameInput={setProductNameInput}
            autoDetectProduct={autoDetectProduct}
            setAutoDetectProduct={setAutoDetectProduct}
            ingestionMode={ingestionMode}
            setIngestionMode={setIngestionMode}
            generateSummary={generateSummary}
            setGenerateSummary={setGenerateSummary}
            handleUploadAndProcess={handleUploadAndProcess}
            selectedFile={selectedFile}
            processing={processing}
          />
        </div>
      </div>

      {/* Progress & Result Banner/Modal */}
      <IngestionProgressModal
        processing={processing}
        pipelineStep={pipelineStep}
        ingestResult={ingestResult}
        navigate={navigate}
      />
    </div>
  );
};

export default DatasetUpload;
