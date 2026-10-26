import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Star,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  MessageSquareQuote,
  TrendingUp,
  BarChart3,
  AlertTriangle,
  Send,
  Globe,
  Smartphone,
  UploadCloud,
  Bot,
  Zap,
  Building2,
  Users,
  Compass,
  Store,
  Utensils,
  Scissors,
  Stethoscope,
  ShoppingBag,
  ExternalLink,
  ChevronRight,
  Flame,
  Clock,
  Layers,
  HeartPulse,
  Award,
  Check,
  CheckCheck
} from 'lucide-react';

const Landing = () => {
  const { isAuthenticated } = useAuth();

  // FAQ Accordion State
  const [openFaq, setOpenFaq] = useState(0);

  const faqs = [
    {
      q: 'What is BrandPulse AI and who is it designed for?',
      a: 'BrandPulse AI is a purpose-built customer reputation and feedback intelligence platform for small and medium businesses—including restaurants, cafes, bakeries, retail shops, salons, and healthcare clinics. It automatically aggregates customer reviews from Google Maps, Instagram comments, and uploaded spreadsheets, translating colloquial feedback (English, Tamil, Hindi) into clear action items and instant WhatsApp reply templates.'
    },
    {
      q: 'Does BrandPulse AI really understand code-mixed languages like Tanglish and Hinglish?',
      a: 'Yes! Unlike generic Western sentiment analyzers that get confused by sentences like "Sappaadu semma taste aana billing late" or "Khana accha tha lekin table clean nahi tha", BrandPulse AI is powered by specialized multilingual NLP models with Indic code-mixed lexicons and XLM-RoBERTa embeddings that accurately score sentiment and extract specific friction keywords.'
    },
    {
      q: 'How does the instant crisis alert system protect my shop rating?',
      a: 'Whenever a customer posts a 1 or 2-star review, or when the AI spots repeated complaints about hygiene, billing, or food temperature within a 2-hour window, BrandPulse AI instantly fires an alert to your phone via WhatsApp, SMS, or Email. This allows you or your store manager to resolve the complaint before it spirals on social media.'
    },
    {
      q: 'Can I import historical reviews from Zomato, Swiggy, or Google Takeout?',
      a: 'Absolutely! Our smart CSV and Excel ingestion engine automatically recognizes column headers from Zomato, Swiggy, Amazon, and Google Places review exports. You can upload thousands of historical reviews in seconds and immediately view multi-month sentiment trends and aspect scores.'
    },
    {
      q: 'How does the "Nearby Competitor Benchmark" work?',
      a: 'You can add 2 to 5 neighboring shops or competitors (via Google Places or custom keywords). BrandPulse AI tracks their public sentiment ratings, highlighting where your business leads (e.g. food taste, friendly service) and where competitors might be gaining an edge (e.g. faster billing, parking availability).'
    },
    {
      q: 'Do I need technical skills or a dedicated IT team?',
      a: 'Zero technical skills required! BrandPulse AI is built phone-first with high-contrast text, clear visual indicators, and a 1-tap WhatsApp response workflow designed specifically for busy local business owners.'
    }
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-800 font-sans selection:bg-blue-600 selection:text-white">
      {/* Top Banner Notice */}
      <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-[#0F172A] text-white text-xs py-2 px-4 text-center border-b border-blue-950 font-medium relative z-50">
        <div className="max-w-7xl mx-auto flex items-center justify-center space-x-2">
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-blue-500/30 text-blue-200 text-[11px] font-bold tracking-wide uppercase border border-blue-400/20">
            <Sparkles className="w-3 h-3 text-blue-300" />
            Active AI Engine
          </span>
          <span className="text-slate-200">
            Hybrid Multilingual Sentiment Intelligence with English, Tanglish & Hinglish Code-Mixed Detection
          </span>
        </div>
      </div>

      {/* Sticky Main Navigation */}
      <nav className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-slate-200 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between">
          {/* Logo & Brand Name */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="relative">
              <img
                src="/logo.jpg"
                alt="BrandPulse AI Logo"
                className="w-10 h-10 rounded-xl object-cover shadow-sm ring-2 ring-blue-600/20 group-hover:ring-blue-600 transition"
              />
              <span className="absolute -bottom-1 -right-1 w-3.5 h-3.5 bg-emerald-500 rounded-full ring-2 ring-white" />
            </div>
            <div>
              <div className="font-extrabold text-lg tracking-tight text-slate-900 flex items-center space-x-1.5">
                <span>BrandPulse</span>
                <span className="text-blue-600">AI</span>
              </div>
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider hidden sm:block">
                Reputation & Review Intelligence
              </p>
            </div>
          </Link>

          {/* Center Navigation Links (Desktop) */}
          <div className="hidden lg:flex items-center space-x-8 text-xs font-bold text-slate-600">
            <a href="#features" className="hover:text-blue-600 transition">
              Key Features
            </a>
            <a href="#omnichannel" className="hover:text-blue-600 transition">
              Omnichannel Sync
            </a>
            <a href="#industries" className="hover:text-blue-600 transition">
              Who It's For
            </a>
            <a href="#faq" className="hover:text-blue-600 transition">
              FAQ
            </a>
          </div>

          {/* Right Action Buttons */}
          <div className="flex items-center space-x-3">
            {isAuthenticated ? (
              <Link
                to="/"
                className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md hover:shadow-lg transition transform hover:-translate-y-0.5"
              >
                <span>Go to Dashboard</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-4 py-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-bold transition"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="inline-flex items-center space-x-1.5 px-4.5 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-extrabold shadow-md hover:shadow-blue-500/25 transition transform hover:-translate-y-0.5"
                >
                  <span>Start Free</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* HERO SECTION */}
      <section className="relative pt-12 pb-20 sm:pt-20 sm:pb-28 overflow-hidden bg-gradient-to-b from-white via-slate-50 to-[#F8FAFC]">
        {/* Glow Spheres */}
        <div className="absolute top-10 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-gradient-to-r from-blue-400/15 via-indigo-400/15 to-purple-400/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -top-24 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-3xl mx-auto space-y-6">
            {/* Pill Badge */}
            <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-bold shadow-xs">
              <span className="w-2 h-2 rounded-full bg-blue-600 animate-ping" />
              <span>Built for Local Shops, Restaurants & Healthcare Clinics</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight leading-[1.12]">
              Turn Customer Reviews Into{' '}
              <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-800 bg-clip-text text-transparent">
                Repeat Visits & Higher Ratings
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-base sm:text-lg text-slate-600 leading-relaxed font-normal max-w-2xl mx-auto">
              BrandPulse AI monitors Google Maps, Instagram, Swiggy, and customer voice notes in{' '}
              <strong className="text-slate-800 font-bold">English, Tamil, and Hindi</strong>. Automatically detect
              billing delays, taste complaints, and friction points—then reply in 1 tap on WhatsApp.
            </p>

            {/* Hero CTAs */}
            <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
              <Link
                to="/register"
                className="w-full sm:w-auto inline-flex items-center justify-center space-x-2.5 px-8 py-3.5 rounded-2xl bg-[#2563EB] hover:bg-[#1E3A8A] text-white text-sm font-extrabold shadow-blue-glow hover:shadow-xl transition transform hover:-translate-y-0.5"
              >
                <span>Get Started Free</span>
                <ArrowRight className="w-4 h-4" />
              </Link>

              <Link
                to="/login"
                className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3.5 rounded-2xl bg-white hover:bg-slate-50 border border-slate-300 text-slate-800 text-sm font-bold shadow-xs hover:border-slate-400 transition"
              >
                <span>Sign In to Your Shop</span>
                <ArrowRight className="w-4 h-4 text-slate-500" />
              </Link>
            </div>

            {/* Micro Trust Points */}
            <div className="pt-4 flex flex-wrap items-center justify-center gap-y-2 gap-x-6 text-xs text-slate-500 font-semibold">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                No credit card required
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                2-minute shop onboarding
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                Phone-first WhatsApp alerts
              </span>
            </div>
          </div>

          {/* ELEGANT HERO PLATFORM SHOWCASE CARD */}
          <div className="mt-12 lg:mt-16 max-w-5xl mx-auto">
            <div className="rounded-3xl border border-slate-200/90 bg-white shadow-2xl p-5 sm:p-7 relative overflow-hidden">
              {/* Card Header Bar */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-5 mb-6 border-b border-slate-100 gap-3">
                <div className="flex items-center space-x-3">
                  <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                    <Store className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <h2 className="text-sm font-extrabold text-slate-900">
                        BrandPulse AI Reputation Hub
                      </h2>
                      <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold border border-emerald-200 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        Active Sync
                      </span>
                    </div>
                    <p className="text-xs text-slate-500">
                      Real-time multichannel sentiment tracking & crisis protection
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2 text-[11px] font-semibold text-slate-600 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200">
                  <span className="text-slate-400">Location:</span>
                  <span className="text-slate-800 font-bold">Main Branch (T. Nagar)</span>
                </div>
              </div>

              {/* Top 3 Real-World KPI Tiles */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                    Net Satisfaction Score
                  </div>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-2xl font-black text-emerald-600">89.4%</span>
                    <span className="text-xs font-bold text-emerald-700 bg-emerald-100/70 px-1.5 py-0.5 rounded">
                      +4.2% this week
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">Based on 1,480+ customer reviews</div>
                </div>

                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                    Multilingual Detection
                  </div>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-2xl font-black text-blue-600">99.4%</span>
                    <span className="text-xs font-bold text-blue-700 bg-blue-100/70 px-1.5 py-0.5 rounded">
                      Indic Models
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">English, Tanglish & Hinglish</div>
                </div>

                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                    Reputation Protection
                  </div>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-2xl font-black text-purple-600">&lt; 3 mins</span>
                    <span className="text-xs font-bold text-purple-700 bg-purple-100/70 px-1.5 py-0.5 rounded">
                      WhatsApp Alerts
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">Instant friction alerts for 1–2★ reviews</div>
                </div>
              </div>

              {/* Showcase Dual Columns: Real Feedback Analysis + 1-Tap WhatsApp Response */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 bg-slate-50/80 rounded-2xl p-4 sm:p-5 border border-slate-200">
                {/* Left: Multilingual Review Breakdown */}
                <div className="lg:col-span-7 space-y-3">
                  <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-2">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-bold text-slate-400 uppercase tracking-wider">
                        Customer Feedback
                      </span>
                      <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-bold text-[10px] border border-blue-200">
                        Tanglish (Tamil + English)
                      </span>
                    </div>
                    <p className="text-xs sm:text-sm text-slate-800 font-medium italic leading-relaxed">
                      "Sappaadu semma taste, especially ghee roast and filter coffee! Aana billing counter la romba
                      neram wait panna vachitaanga, 20 mins delay."
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="bg-white p-3 rounded-xl border border-slate-200">
                      <span className="text-[10px] font-bold text-slate-400 uppercase block mb-1">
                        Praise Aspects
                      </span>
                      <span className="font-semibold text-emerald-700">Ghee Roast & Filter Coffee</span>
                    </div>
                    <div className="bg-white p-3 rounded-xl border border-slate-200">
                      <span className="text-[10px] font-bold text-slate-400 uppercase block mb-1">
                        Friction Flag
                      </span>
                      <span className="font-semibold text-amber-700">Billing Counter Queue (20 min)</span>
                    </div>
                  </div>
                </div>

                {/* Right: AI WhatsApp Reply Template */}
                <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-col justify-between space-y-3">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                      <div className="flex items-center space-x-1.5">
                        <Smartphone className="w-3.5 h-3.5 text-emerald-600" />
                        <span className="text-xs font-bold text-slate-900">
                          1-Tap WhatsApp Response
                        </span>
                      </div>
                      <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                        Auto-Drafted
                      </span>
                    </div>

                    <p className="text-xs text-slate-700 bg-[#E7F6ED]/40 p-3 rounded-xl border border-emerald-200/60 leading-relaxed font-medium">
                      "Vanakkam! Thank you so much for loving our ghee roast and filter coffee. We sincerely apologize
                      for the billing counter delay today. We are adding an extra billing terminal during rush hours
                      immediately. Please visit us again soon! 🙏"
                    </p>
                  </div>

                  <div className="pt-1 flex items-center justify-between text-[11px] text-slate-500">
                    <span className="flex items-center gap-1 text-emerald-600 font-semibold">
                      <CheckCheck className="w-4 h-4" /> Ready to send
                    </span>
                    <Link
                      to="/register"
                      className="font-bold text-blue-600 hover:text-blue-700 hover:underline"
                    >
                      Connect your shop →
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* STATS & METRICS BAR */}
      <section className="bg-slate-900 text-white py-10 border-y border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            <div>
              <div className="text-3xl sm:text-4xl font-black font-mono text-blue-400">99.4%</div>
              <div className="text-xs sm:text-sm text-slate-400 mt-1 font-medium">
                Sentiment Accuracy (Indic & English)
              </div>
            </div>
            <div>
              <div className="text-3xl sm:text-4xl font-black font-mono text-emerald-400">10x</div>
              <div className="text-xs sm:text-sm text-slate-400 mt-1 font-medium">
                Faster Crisis Resolution
              </div>
            </div>
            <div>
              <div className="text-3xl sm:text-4xl font-black font-mono text-amber-400">0.6★</div>
              <div className="text-xs sm:text-sm text-slate-400 mt-1 font-medium">
                Average Google Rating Boost
              </div>
            </div>
            <div>
              <div className="text-3xl sm:text-4xl font-black font-mono text-purple-400">2 min</div>
              <div className="text-xs sm:text-sm text-slate-400 mt-1 font-medium">
                Shop Setup & Historical Ingestion
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* THREE ESSENTIAL OWNER QUESTIONS */}
      <section className="py-16 sm:py-24 bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14 space-y-3">
            <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">
              The 3 Daily Questions Every Owner Asks
            </span>
            <h2 className="text-2xl sm:text-4xl font-black text-slate-900 tracking-tight">
              Answer What Matters in 30 Seconds Every Morning
            </h2>
            <p className="text-sm text-slate-500">
              No complicated graphs or confusing corporate jargon. We distill hundreds of reviews into 3 simple,
              actionable answers.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Card 1 */}
            <div className="p-6 rounded-2xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:shadow-xl transition group">
              <div className="w-12 h-12 rounded-2xl bg-blue-100 text-blue-600 flex items-center justify-center font-black text-lg mb-4 group-hover:scale-110 transition">
                1
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">
                What are customers saying?
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                Discover your true Net Satisfaction Score, top praised dishes or products, and emotional trends
                without reading hundreds of individual reviews manually.
              </p>
              <div className="mt-4 pt-4 border-t border-slate-200 text-xs font-semibold text-blue-600 flex items-center gap-1">
                <span>Sentiment & Aspect Scoring</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </div>
            </div>

            {/* Card 2 */}
            <div className="p-6 rounded-2xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:shadow-xl transition group">
              <div className="w-12 h-12 rounded-2xl bg-amber-100 text-amber-600 flex items-center justify-center font-black text-lg mb-4 group-hover:scale-110 transition">
                2
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">
                What is going wrong?
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                Pinpoint exact operational friction points—such as slow billing, cold food, broken AC, or rude
                checkout staff—before they damage your reputation.
              </p>
              <div className="mt-4 pt-4 border-t border-slate-200 text-xs font-semibold text-amber-600 flex items-center gap-1">
                <span>Instant Friction & Crisis Alerts</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </div>
            </div>

            {/* Card 3 */}
            <div className="p-6 rounded-2xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:shadow-xl transition group">
              <div className="w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-600 flex items-center justify-center font-black text-lg mb-4 group-hover:scale-110 transition">
                3
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">
                What should I do right now?
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                Receive prioritized action steps for store staff and polite, pre-crafted WhatsApp customer apology
                templates ready to send with 1 click.
              </p>
              <div className="mt-4 pt-4 border-t border-slate-200 text-xs font-semibold text-emerald-600 flex items-center gap-1">
                <span>1-Tap Response Templates</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CORE FEATURES GRID (Anchor: #features) */}
      <section id="features" className="py-16 sm:py-24 bg-[#F8FAFC]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
            <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">
              Comprehensive Intelligence Suite
            </span>
            <h2 className="text-2xl sm:text-4xl font-black text-slate-900 tracking-tight">
              Engineered Specifically For Real-World Shop Operations
            </h2>
            <p className="text-sm text-slate-500">
              Everything you need to monitor, analyze, and elevate your local business presence across all modern
              channels.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Feature 1 */}
            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs hover:shadow-xl transition group">
              <div className="w-11 h-11 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-4 group-hover:bg-blue-600 group-hover:text-white transition">
                <Globe className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-1.5">
                Multilingual & Tanglish/Hinglish NLP
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                Native support for English, Tamil, Tanglish, Hindi, and Hinglish. Never miss colloquial praise or
                customer frustration written in local dialects.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs hover:shadow-xl transition group">
              <div className="w-11 h-11 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center mb-4 group-hover:bg-purple-600 group-hover:text-white transition">
                <Bot className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-1.5">
                "Ask AI" Shop Advisor Copilot
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                Chat with an intelligent assistant about your store: "Why did ratings drop on Friday?", "What do
                customers think of the new branch?", or "Draft an apology message."
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs hover:shadow-xl transition group">
              <div className="w-11 h-11 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4 group-hover:bg-emerald-600 group-hover:text-white transition">
                <BarChart3 className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-1.5">
                Nearby Shop Benchmarking
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                Benchmark against 2 to 5 actual nearby competitors. Compare food taste, pricing perception, wait
                times, and overall store satisfaction side-by-side.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs hover:shadow-xl transition group">
              <div className="w-11 h-11 rounded-xl bg-red-50 text-red-600 flex items-center justify-center mb-4 group-hover:bg-red-600 group-hover:text-white transition">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-1.5">
                Early-Warning Crisis Alerts
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                Automated instant triggers for 1–2 star reviews and negative complaint spikes delivered straight to
                your phone via WhatsApp, SMS, or Email.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs hover:shadow-xl transition group">
              <div className="w-11 h-11 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-4 group-hover:bg-indigo-600 group-hover:text-white transition">
                <UploadCloud className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-1.5">
                Bulk CSV / Excel & Audio Ingest
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                Upload historical spreadsheets from Zomato, Swiggy, Amazon, and Google Maps in seconds, plus
                transcription for WhatsApp customer audio voice notes.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs hover:shadow-xl transition group">
              <div className="w-11 h-11 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center mb-4 group-hover:bg-amber-600 group-hover:text-white transition">
                <Smartphone className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-1.5">
                Mobile-First One-Handed UI
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                Clean, high-contrast interface with a dedicated mobile bottom navigation bar designed specifically
                for quick one-handed check-ins between customer orders.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* OMNICHANNEL INGESTION SHOWCASE (Anchor: #omnichannel) */}
      <section id="omnichannel" className="py-16 sm:py-24 bg-white border-y border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            <div className="lg:col-span-5 space-y-5">
              <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">
                Seamless Omnichannel Sync
              </span>
              <h2 className="text-2xl sm:text-4xl font-black text-slate-900 tracking-tight leading-tight">
                All Customer Conversations In One Single Hub
              </h2>
              <p className="text-sm text-slate-600 leading-relaxed">
                Stop jumping between Google Maps, Instagram, Swiggy, and WhatsApp. BrandPulse AI unifies all reviews
                and feedback into an automatic, real-time feed with smart aspect tagging.
              </p>

              <div className="space-y-3 pt-2">
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0 mt-0.5">
                    <Check className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-900">Google Places / Business Profile</h4>
                    <p className="text-[11px] text-slate-500">Live sync for ratings, reviews, and star updates</p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0 mt-0.5">
                    <Check className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-900">Instagram Business & Meta Graph API</h4>
                    <p className="text-[11px] text-slate-500">Syncs post comments, reels feedback, and mentions</p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0 mt-0.5">
                    <Check className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-900">Bulk CSV & Excel Ingestion</h4>
                    <p className="text-[11px] text-slate-500">Auto-detects columns from Zomato, Swiggy, and CSVs</p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0 mt-0.5">
                    <Check className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-900">WhatsApp Voice Note Transcription</h4>
                    <p className="text-[11px] text-slate-500">Converts voice messages into structured sentiment</p>
                  </div>
                </div>
              </div>

              <div className="pt-2">
                <Link
                  to="/register"
                  className="inline-flex items-center space-x-2 text-xs font-bold text-blue-600 hover:text-blue-700"
                >
                  <span>Connect your first channel in under 2 minutes</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            {/* Visual Feed Simulation Card */}
            <div className="lg:col-span-7">
              <div className="bg-slate-900 rounded-3xl p-5 sm:p-6 shadow-2xl text-slate-200 border border-slate-800 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full bg-red-500" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500" />
                    <div className="w-3 h-3 rounded-full bg-emerald-500" />
                    <span className="text-xs font-mono text-slate-400 ml-2">Live Unified Mention Feed</span>
                  </div>
                  <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/70 border border-emerald-800 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    AUTO-SYNCING
                  </span>
                </div>

                {/* Simulated Feed Items */}
                <div className="space-y-3">
                  {/* Item 1: Google */}
                  <div className="p-3.5 rounded-xl bg-slate-800/80 border border-slate-700 flex items-start justify-between gap-3">
                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-0.5 rounded bg-blue-900/60 text-blue-300 text-[10px] font-bold">
                          Google Maps
                        </span>
                        <div className="flex text-amber-400 text-xs">★★★★★</div>
                        <span className="text-[10px] text-slate-400">Praveen K. • 4 mins ago</span>
                      </div>
                      <p className="text-xs text-slate-200 line-clamp-1">
                        "Filter coffee is divine! Best South Indian breakfast spot in town."
                      </p>
                    </div>
                    <span className="px-2 py-1 rounded bg-emerald-900/50 text-emerald-300 text-[10px] font-bold shrink-0">
                      +96 Positive
                    </span>
                  </div>

                  {/* Item 2: Instagram */}
                  <div className="p-3.5 rounded-xl bg-slate-800/80 border border-slate-700 flex items-start justify-between gap-3">
                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-0.5 rounded bg-pink-900/60 text-pink-300 text-[10px] font-bold">
                          Instagram Reel
                        </span>
                        <span className="text-[10px] text-slate-400">@chennaifoodie • 22 mins ago</span>
                      </div>
                      <p className="text-xs text-slate-200 line-clamp-1">
                        "Loved the food presentation! Semma ghee roast. But pls fix AC near window."
                      </p>
                    </div>
                    <span className="px-2 py-1 rounded bg-amber-900/50 text-amber-300 text-[10px] font-bold shrink-0">
                      Friction: AC
                    </span>
                  </div>

                  {/* Item 3: CSV Import */}
                  <div className="p-3.5 rounded-xl bg-slate-800/80 border border-slate-700 flex items-start justify-between gap-3">
                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-0.5 rounded bg-orange-900/60 text-orange-300 text-[10px] font-bold">
                          Swiggy / Zomato
                        </span>
                        <div className="flex text-amber-400 text-xs">★★★★☆</div>
                        <span className="text-[10px] text-slate-400">Order #88219 • 1 hr ago</span>
                      </div>
                      <p className="text-xs text-slate-200 line-clamp-1">
                        "Packing was neat and delivery was on time. Chutney quantity was generous."
                      </p>
                    </div>
                    <span className="px-2 py-1 rounded bg-emerald-900/50 text-emerald-300 text-[10px] font-bold shrink-0">
                      +88 Positive
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* WHO IT'S FOR / INDUSTRIES (Anchor: #industries) */}
      <section id="industries" className="py-16 sm:py-24 bg-[#F8FAFC]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-14 space-y-3">
            <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">Tailored Verticals</span>
            <h2 className="text-2xl sm:text-4xl font-black text-slate-900 tracking-tight">
              Built For Your Exact Business Category
            </h2>
            <p className="text-sm text-slate-500">
              Each industry has unique friction points. BrandPulse AI comes pre-trained with custom aspect taxonomies.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Restaurant */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs hover:border-blue-400 transition space-y-3">
              <div className="w-10 h-10 rounded-xl bg-orange-50 text-orange-600 flex items-center justify-center font-bold">
                <Utensils className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-slate-900 text-base">Restaurants & Cafes</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Track food taste consistency, portion sizes, peak-hour billing delays, hygiene, and delivery packaging.
              </p>
              <div className="text-[11px] font-semibold text-orange-600">
                Common aspects: Taste, Wait Time, AC, Billing
              </div>
            </div>

            {/* Retail & Grocery */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs hover:border-blue-400 transition space-y-3">
              <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                <ShoppingBag className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-slate-900 text-base">Retail & Supermarkets</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Monitor checkout wait times, stock availability, pricing transparency, and cashier courtesy.
              </p>
              <div className="text-[11px] font-semibold text-blue-600">
                Common aspects: Checkout Speed, Stock, Pricing
              </div>
            </div>

            {/* Clinics */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs hover:border-blue-400 transition space-y-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
                <Stethoscope className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-slate-900 text-base">Clinics & Healthcare</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Assess patient appointment wait times, doctor bedside manners, receptionist courtesy, and clinic
                cleanliness.
              </p>
              <div className="text-[11px] font-semibold text-emerald-600">
                Common aspects: Doctor Care, Wait Time, Hygiene
              </div>
            </div>

            {/* Salons & Spas */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs hover:border-blue-400 transition space-y-3">
              <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold">
                <Scissors className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-slate-900 text-base">Salons & Wellness</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Track stylist performance, service quality, hygiene of equipment, appointment scheduling, and customer
                comfort.
              </p>
              <div className="text-[11px] font-semibold text-purple-600">
                Common aspects: Stylist Skill, Cleanliness, Comfort
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ SECTION (Anchor: #faq) */}
      <section id="faq" className="py-16 sm:py-24 bg-white border-y border-slate-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14 space-y-3">
            <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">
              Answers to Common Questions
            </span>
            <h2 className="text-2xl sm:text-4xl font-black text-slate-900 tracking-tight">
              Frequently Asked Questions
            </h2>
            <p className="text-sm text-slate-500">
              Everything you need to know about setting up and running BrandPulse AI for your business.
            </p>
          </div>

          <div className="space-y-4">
            {faqs.map((faq, index) => {
              const isOpen = openFaq === index;
              return (
                <div
                  key={index}
                  className="rounded-2xl border border-slate-200 bg-slate-50/50 overflow-hidden shadow-xs transition"
                >
                  <button
                    type="button"
                    onClick={() => setOpenFaq(isOpen ? -1 : index)}
                    className="w-full text-left p-5 flex items-center justify-between text-xs sm:text-sm font-bold text-slate-900 hover:text-blue-600 transition"
                  >
                    <span>{faq.q}</span>
                    {isOpen ? (
                      <ChevronUp className="w-4 h-4 text-slate-400 shrink-0 ml-2" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-slate-400 shrink-0 ml-2" />
                    )}
                  </button>
                  {isOpen && (
                    <div className="px-5 pb-5 text-xs text-slate-600 leading-relaxed border-t border-slate-200/60 pt-3">
                      {faq.a}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* BOTTOM HIGH-IMPACT CTA BANNER */}
      <section className="bg-gradient-to-r from-blue-900 via-indigo-900 to-[#0F172A] text-white py-16 sm:py-20 relative overflow-hidden">
        {/* Glow Effects */}
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10 space-y-6">
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-blue-500/20 text-blue-200 text-xs font-bold border border-blue-400/20">
            <Award className="w-3.5 h-3.5 text-blue-300" />
            <span>Protect Your Rating Today</span>
          </div>

          <h2 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
            Stop Guessing What Your Customers Think.
            <br />
            <span className="text-blue-400">Start Knowing and Growing.</span>
          </h2>

          <p className="text-sm sm:text-base text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Join hundreds of local restaurants, bakeries, salons, and healthcare clinics using BrandPulse AI to
            protect their reputation and turn feedback into loyal repeat visits.
          </p>

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              to="/register"
              className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-8 py-3.5 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-extrabold text-sm shadow-xl transition transform hover:-translate-y-0.5"
            >
              <span>Get Started Free</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              to="/login"
              className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3.5 rounded-2xl bg-slate-800/80 hover:bg-slate-800 border border-slate-700 text-slate-200 font-bold text-sm transition"
            >
              <span>Sign In to Your Shop</span>
              <ArrowRight className="w-4 h-4 text-slate-400" />
            </Link>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="bg-slate-950 text-slate-400 text-xs py-12 border-t border-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8 pb-8 border-b border-slate-900">
            {/* Col 1: Brand Info */}
            <div className="space-y-3">
              <div className="flex items-center space-x-2.5">
                <img
                  src="/logo.jpg"
                  alt="BrandPulse AI Logo"
                  className="w-8 h-8 rounded-lg object-cover ring-1 ring-blue-500/30"
                />
                <span className="font-extrabold text-base text-white tracking-tight">
                  BrandPulse <span className="text-blue-500">AI</span>
                </span>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Real-World AI Customer Feedback & Reputation Intelligence for Small Businesses & Local Shops.
              </p>
              <div className="flex items-center space-x-2 pt-1 text-[11px] text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span>All AI Models & MongoDB Atlas Operational</span>
              </div>
            </div>

            {/* Col 2: Product */}
            <div className="space-y-2">
              <div className="font-bold text-slate-200 text-xs uppercase tracking-wider">Product</div>
              <ul className="space-y-1.5 text-[11px]">
                <li>
                  <a href="#features" className="hover:text-white transition">
                    Key Features
                  </a>
                </li>
                <li>
                  <a href="#omnichannel" className="hover:text-white transition">
                    Omnichannel Ingestion
                  </a>
                </li>
                <li>
                  <a href="#industries" className="hover:text-white transition">
                    Who It's For
                  </a>
                </li>
                <li>
                  <a href="#faq" className="hover:text-white transition">
                    FAQ
                  </a>
                </li>
                <li>
                  <Link to="/login" className="hover:text-white transition">
                    Sign In
                  </Link>
                </li>
              </ul>
            </div>

            {/* Col 3: Integrations */}
            <div className="space-y-2">
              <div className="font-bold text-slate-200 text-xs uppercase tracking-wider">Integrations</div>
              <ul className="space-y-1.5 text-[11px]">
                <li>Google Maps & Places API</li>
                <li>Instagram Business Graph API</li>
                <li>Bulk CSV & Swiggy/Zomato Importer</li>
                <li>WhatsApp & Twilio Notifications</li>
                <li>Resend & SMTP Email Alerts</li>
              </ul>
            </div>

            {/* Col 4: Architecture */}
            <div className="space-y-2">
              <div className="font-bold text-slate-200 text-xs uppercase tracking-wider">Technology Stack</div>
              <ul className="space-y-1.5 text-[11px]">
                <li>FastAPI & Async MongoDB Motor</li>
                <li>React 18 & Vite & Tailwind CSS</li>
                <li>Indic Code-Mixed NLP & XLM-RoBERTa</li>
                <li>Hybrid Local Scikit-Learn + LLM Engine</li>
                <li>Multi-Tenant JWT Isolation</li>
              </ul>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between text-[11px] text-slate-500 gap-3">
            <p>© {new Date().getFullYear()} BrandPulse AI. Built with precision for local business owners.</p>
            <div className="flex items-center space-x-4">
              <span>English • தமிழ் • हिन्दी</span>
              <span>•</span>
              <Link to="/login" className="hover:text-slate-300">
                Staff Portal
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
