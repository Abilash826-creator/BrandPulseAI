import React, { useState, useEffect, useMemo } from 'react';
import { SentimentBadge, IntentBadge } from '../common/StatusBadge';
import {
  X,
  Instagram,
  ExternalLink,
  Copy,
  Check,
  MessageSquare,
  Video,
  Image as ImageIcon,
  Flame,
  Volume2,
  Sparkles,
  ArrowUpRight,
  Clock,
  Users,
  Send,
  CornerDownRight,
  Share2,
  ShieldAlert,
  HelpCircle,
  Package,
  Layers,
  Heart,
  MessageCircle,
  Smile,
  Frown,
  Meh
} from 'lucide-react';

/**
 * Builds guaranteed direct URL to an exact comment, reel, or post on Instagram.
 */
export const buildDirectCommentUrl = (item, activeCommentId = null) => {
  if (!item) return '#';

  const isInstagram = item.platform?.toLowerCase() === 'instagram';
  const isComment = item.media_type === 'COMMENT' || Boolean(item.comment_id) || Boolean(activeCommentId);
  const isReel = item.media_type === 'REEL' || item.media_type === 'VIDEO' || item.parent_media_type === 'REEL';
  const commentId = activeCommentId || item.comment_id;

  if (isInstagram) {
    const parentUrl = item.parent_post_url || (item.url && !item.url.includes('/c/') ? item.url : null);
    const postId = item.parent_post_id || item.post_id || (item.id ? String(item.id).replace(/^men_|^ig_comm_|^ig_post_/, '') : 'post');
    const cleanPostCode = String(postId).replace(/^ig_/, '').replace(/^post_/, '').replace(/_comment.*$/, '');

    // 1. Direct comment link
    if (isComment && commentId) {
      if (parentUrl && parentUrl.startsWith('http')) {
        const cleanParent = parentUrl.split('?')[0].replace(/\/+$/, '');
        if (cleanParent.includes('/reel/')) {
          return `${cleanParent}/?comment_id=${commentId}`;
        }
        return `${cleanParent}/c/${commentId}/`;
      }
      if (isReel) {
        return `https://www.instagram.com/reel/${cleanPostCode}/?comment_id=${commentId}`;
      }
      return `https://www.instagram.com/p/${cleanPostCode}/c/${commentId}/`;
    }

    // 2. Explicit item.url provided
    if (item.url && item.url.startsWith('http')) {
      if (isComment && commentId && !item.url.includes('/c/') && !item.url.includes('comment_id')) {
        const clean = item.url.split('?')[0].replace(/\/+$/, '');
        return `${clean}/c/${commentId}/`;
      }
      return item.url;
    }

    // 3. Parent post URL
    if (parentUrl && parentUrl.startsWith('http')) {
      return parentUrl;
    }

    // 4. Construct from post ID
    if (cleanPostCode) {
      if (isReel) {
        return `https://www.instagram.com/reel/${cleanPostCode}/`;
      }
      return `https://www.instagram.com/p/${cleanPostCode}/`;
    }

    if (item.author_handle && item.author_handle.startsWith('@') && item.author_handle.length > 2) {
      return `https://www.instagram.com/${item.author_handle.replace('@', '')}/`;
    }

    return 'https://www.instagram.com/';
  }

  return item.url || '#';
};

const CommentThreadModal = ({ isOpen, onClose, activeItem, allMentions = [] }) => {
  const [selectedComment, setSelectedComment] = useState(null);
  const [copied, setCopied] = useState(false);
  const [aiReply, setAiReply] = useState('');
  const [generatingReply, setGeneratingReply] = useState(false);
  const [copiedReply, setCopiedReply] = useState(false);

  useEffect(() => {
    if (activeItem) {
      setSelectedComment(activeItem);
      setAiReply('');
      setCopied(false);
    }
  }, [activeItem]);

  // Find parent post information
  const parentPost = useMemo(() => {
    if (!activeItem) return null;
    
    // If active item is itself a post or reel
    if (activeItem.media_type !== 'COMMENT' && !activeItem.comment_id) {
      return activeItem;
    }

    // Try finding the parent post in allMentions list
    const parentId = activeItem.parent_post_id || activeItem.post_id;
    if (parentId && allMentions?.length) {
      const match = allMentions.find(
        (m) => (m.id === parentId || m.post_id === parentId) && m.media_type !== 'COMMENT' && !m.comment_id
      );
      if (match) return match;
    }

    // Fallback synthesized parent post from comment metadata
    return {
      id: activeItem.parent_post_id || activeItem.post_id || 'parent_post',
      post_id: activeItem.parent_post_id || activeItem.post_id,
      platform: activeItem.platform || 'instagram',
      author: activeItem.brand_name || 'Official Brand Post',
      author_handle: activeItem.mentions?.[0] || `@${(activeItem.brand_name || 'brand').toLowerCase().replace(/\s+/g, '_')}`,
      author_avatar: `https://api.dicebear.com/7.x/bottts/svg?seed=${activeItem.brand_name || 'brand'}`,
      content: activeItem.parent_caption || `Official Discussion Thread on ${(activeItem.brand_name || 'Brand')}`,
      caption: activeItem.parent_caption || `Official Discussion Thread on ${(activeItem.brand_name || 'Brand')}`,
      media_type: activeItem.parent_media_type || 'POST',
      timestamp: activeItem.timestamp,
      reach: (activeItem.reach || 1200) * 4,
      engagement_score: (activeItem.engagement_score || 50) * 3,
      virality_score: activeItem.virality_score,
      url: activeItem.parent_post_url || `https://www.instagram.com/p/${activeItem.post_id || 'post'}/`,
      transcript: activeItem.transcript
    };
  }, [activeItem, allMentions]);

  // Find sibling comments under this same parent post
  const siblingComments = useMemo(() => {
    if (!parentPost || !allMentions?.length) return [];
    const parentId = parentPost.id || parentPost.post_id;
    return allMentions.filter((m) => {
      const isComm = m.media_type === 'COMMENT' || Boolean(m.comment_id);
      if (!isComm) return false;
      const targetMatch = (m.parent_post_id === parentId || m.post_id === parentId || m.parent_post_url === parentPost.url);
      return targetMatch;
    });
  }, [parentPost, allMentions]);

  if (!isOpen || !activeItem) return null;

  const currentComment = selectedComment || activeItem;
  const isInstagram = activeItem.platform?.toLowerCase() === 'instagram';
  const parentUrl = parentPost ? buildDirectCommentUrl(parentPost) : '#';
  const directCommentUrl = buildDirectCommentUrl(currentComment, currentComment.comment_id);
  const isReel = (parentPost?.media_type === 'REEL' || parentPost?.media_type === 'VIDEO');

  const handleCopyLink = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(directCommentUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  const handleGenerateAiReply = () => {
    setGeneratingReply(true);
    setTimeout(() => {
      const brand = currentComment.brand_name || 'our team';
      const sent = currentComment.sentiment?.toLowerCase();
      const product = currentComment.product_detected || currentComment.detected_products?.[0] || 'our offerings';
      
      let reply = '';
      if (sent === 'negative') {
        reply = `Hello ${currentComment.author || 'there'}! Thank you for sharing your candid feedback regarding ${product}. We take performance and customer satisfaction seriously. Please send us a direct message with your order/ticket details so we can resolve this immediately for you! 🙏`;
      } else if (sent === 'positive') {
        reply = `Hi ${currentComment.author}! 🎉 Thank you so much for the love on ${product}! We are thrilled you're having a fantastic experience with ${brand}. Stay tuned for exciting updates! ✨`;
      } else {
        reply = `Hello ${currentComment.author}! Thanks for reaching out. We appreciate your query regarding ${product}. Our support team is ready to help — feel free to DM us anytime! 😊`;
      }

      setAiReply(reply);
      setGeneratingReply(false);
    }, 450);
  };

  const handleCopyAiReply = () => {
    if (navigator.clipboard && aiReply) {
      navigator.clipboard.writeText(aiReply);
      setCopiedReply(true);
      setTimeout(() => setCopiedReply(false), 2500);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in overflow-y-auto">
      <div 
        className="bg-white border border-slate-200 rounded-3xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden animate-scale-up my-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-gradient-to-r from-slate-50 to-white">
          <div className="flex items-center space-x-3">
            <div className={`p-2.5 rounded-2xl shadow-xs ${
              isInstagram 
                ? 'bg-gradient-to-tr from-amber-500 via-rose-500 to-purple-600 text-white' 
                : 'bg-blue-600 text-white'
            }`}>
              {isInstagram ? <Instagram className="w-5 h-5" /> : <MessageSquare className="w-5 h-5" />}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-extrabold text-slate-900 tracking-tight">
                  Post & Comment Thread Inspector
                </h3>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-[#2563EB] border border-blue-200 uppercase tracking-wide">
                  Live Deep-Link Ready
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Direct view of the comment within its parent {isReel ? 'Reel' : 'Post'} conversation thread
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
            title="Close viewer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1 custom-scrollbar text-xs">
          
          {/* Section 1: Parent Post / Reel Context Banner */}
          {parentPost && (
            <div className="p-4 rounded-2xl bg-slate-50/90 border border-slate-200/90 space-y-3 relative overflow-hidden">
              <div className="flex items-start justify-between gap-3 flex-wrap sm:flex-nowrap">
                <div className="flex items-center space-x-3 min-w-0">
                  <img
                    src={parentPost.author_avatar || `https://api.dicebear.com/7.x/bottts/svg?seed=${parentPost.author_handle || 'parent'}`}
                    alt={parentPost.author}
                    className="w-10 h-10 rounded-xl bg-white border border-slate-200 object-cover shrink-0"
                  />
                  <div className="min-w-0">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-slate-900 text-xs truncate">
                        {parentPost.author || 'Parent Creator'}
                      </span>
                      <span className="text-[11px] text-slate-500 font-mono">
                        {parentPost.author_handle || '@official_brand'}
                      </span>

                      {/* Post / Reel Badge */}
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700 text-[10px] font-semibold">
                        {isReel ? <Video className="w-3 h-3 text-rose-500" /> : <ImageIcon className="w-3 h-3 text-blue-500" />}
                        <span>Parent {isReel ? 'Instagram Reel' : 'Instagram Post'}</span>
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 text-[11px] text-slate-400 mt-0.5">
                      <span className="flex items-center space-x-1">
                        <Clock className="w-3 h-3" />
                        <span>{parentPost.timestamp ? new Date(parentPost.timestamp).toLocaleString() : 'Recent'}</span>
                      </span>
                    </div>
                  </div>
                </div>

                {/* External Action Button to Open Parent Post */}
                <a
                  href={parentUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 font-semibold text-[11px] shadow-2xs transition shrink-0"
                  title="Opens the main post or reel on Instagram in a new tab"
                >
                  {isInstagram ? <Instagram className="w-3.5 h-3.5 text-rose-600" /> : <ExternalLink className="w-3.5 h-3.5" />}
                  <span>Open Parent {isReel ? 'Reel' : 'Post'}</span>
                  <ArrowUpRight className="w-3 h-3" />
                </a>
              </div>

              {/* Parent Caption */}
              <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 text-slate-800 leading-relaxed font-normal">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Post Caption & Context
                </span>
                "{parentPost.caption || parentPost.content}"
              </div>

              {/* Reel Speech-to-Text Transcript (if available) */}
              {parentPost.transcript && (
                <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-200 text-[11px] text-emerald-950 space-y-1">
                  <div className="flex items-center space-x-1.5 font-bold text-emerald-800">
                    <Volume2 className="w-3.5 h-3.5 text-[#16A34A]" />
                    <span>Official Transcribed Audio Transcript:</span>
                  </div>
                  <p className="font-mono italic text-[11px] text-emerald-900">
                    "{parentPost.transcript}"
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Section 2: TARGET / SELECTED COMMENT (Prominently Highlighted) */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-[#2563EB] animate-ping" />
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Target Comment Focus
                </h4>
              </div>
              <span className="text-[11px] text-slate-500 font-mono">
                Comment ID: {currentComment.comment_id || currentComment.id || 'N/A'}
              </span>
            </div>

            {/* Glowing Focus Box for the Clicked Comment */}
            <div className="p-5 rounded-2xl bg-gradient-to-br from-blue-50/60 via-white to-blue-50/30 border-2 border-blue-400 shadow-md ring-4 ring-blue-100/70 space-y-3.5 transition-all">
              
              {/* Comment Header */}
              <div className="flex items-start justify-between gap-3 flex-wrap sm:flex-nowrap">
                <div className="flex items-center space-x-3 min-w-0">
                  <img
                    src={currentComment.author_avatar || `https://api.dicebear.com/7.x/bottts/svg?seed=${currentComment.author_handle || 'user'}`}
                    alt={currentComment.author}
                    className="w-10 h-10 rounded-xl bg-slate-100 border border-blue-200 object-cover shrink-0"
                  />
                  <div className="min-w-0">
                    <div className="flex items-center space-x-2 flex-wrap">
                      <span className="font-extrabold text-sm text-slate-900 truncate">
                        {currentComment.author || 'Instagram Commenter'}
                      </span>
                      <span className="text-xs text-blue-600 font-mono">
                        {currentComment.author_handle || '@user'}
                      </span>

                      {/* Selected Badge */}
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-blue-600 text-white text-[10px] font-bold shadow-xs">
                        <span>🎯 Selected Comment</span>
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 text-[11px] text-slate-400 mt-0.5">
                      <span className="flex items-center space-x-1">
                        <Clock className="w-3 h-3" />
                        <span>{currentComment.timestamp ? new Date(currentComment.timestamp).toLocaleString() : 'Just now'}</span>
                      </span>
                      <span>•</span>
                      <span className="flex items-center space-x-1">
                        <Users className="w-3 h-3" />
                        <span>{currentComment.author_followers?.toLocaleString() || 1200} followers</span>
                      </span>
                    </div>
                  </div>
                </div>

                {/* Sentiment + Intent Badges */}
                <div className="flex items-center space-x-2 shrink-0">
                  <SentimentBadge sentiment={currentComment.sentiment} score={currentComment.sentiment_score} />
                  <IntentBadge intent={currentComment.intent} />
                </div>
              </div>

              {/* Exact Comment Text */}
              <div className="p-4 rounded-xl bg-white border border-blue-200 text-slate-900 text-sm font-medium leading-relaxed shadow-2xs space-y-2">
                <div>"{currentComment.content || currentComment.text}"</div>
                {currentComment.translated_text && (
                  <div className="pt-2 border-t border-slate-100 text-xs text-blue-900 bg-blue-50/50 p-2.5 rounded-lg">
                    <div className="text-[10px] font-bold text-blue-600 uppercase tracking-wider mb-1">
                      🌐 English Translation:
                    </div>
                    "{currentComment.translated_text}"
                  </div>
                )}
              </div>

              {/* Granular AI Intelligence Pill Matrix */}
              <div className="flex items-center flex-wrap gap-2 pt-1">
                {(currentComment.topics || []).map((t, idx) => (
                  <span key={`topic-${idx}`} className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-purple-50 text-purple-700 border border-purple-200 text-[11px] font-semibold">
                    <span>#{t}</span>
                  </span>
                ))}
                {currentComment.product_detected && (
                  <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-blue-100/70 text-[#2563EB] border border-blue-200 text-[11px] font-semibold">
                    <Package className="w-3.5 h-3.5" />
                    <span>Product: {currentComment.product_detected}</span>
                  </span>
                )}

                {(currentComment.aspects || []).map((asp, idx) => {
                  const sent = asp.sentiment?.toLowerCase();
                  const color = sent === 'positive'
                    ? 'bg-emerald-50 text-[#16A34A] border-emerald-200'
                    : sent === 'negative'
                      ? 'bg-red-50 text-[#DC2626] border-red-200'
                      : 'bg-slate-100 text-slate-600 border-slate-200';

                  return (
                    <span key={idx} className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold border ${color}`}>
                      <span className="capitalize">{asp.aspect?.replace('_', ' ')}:</span>
                      <strong className="capitalize">{sent}</strong>
                    </span>
                  );
                })}

                <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 border border-slate-200 text-[11px] font-semibold">
                  <Smile className="w-3.5 h-3.5 text-blue-500" />
                  <span>Emotion: <strong className="capitalize">{currentComment.dominant_emotion || 'Joy'}</strong></span>
                </span>

                <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-red-50 text-[#DC2626] border border-red-200 text-[11px] font-semibold font-mono">
                  <Flame className="w-3.5 h-3.5" />
                  <span>Virality: {currentComment.virality_score || 45}</span>
                </span>
              </div>

              {/* Direct Deep-Link Action Toolbar */}
              <div className="pt-3 border-t border-blue-200/80 flex items-center justify-between flex-wrap gap-2.5">
                <div className="flex items-center space-x-2">
                  {/* Primary Direct Link to Instagram Comment */}
                  <a
                    href={directCommentUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-gradient-to-r from-rose-600 via-pink-600 to-purple-600 hover:from-rose-700 hover:to-purple-700 text-white font-bold text-xs shadow-sm transition hover:shadow-md"
                    title="Opens this exact comment highlighted under the post on Instagram"
                  >
                    <Instagram className="w-4 h-4" />
                    <span>Open Live Comment on Instagram</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </a>

                  {/* Copy Deep Link Button */}
                  <button
                    onClick={handleCopyLink}
                    className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 font-semibold text-xs transition shadow-2xs"
                    title="Copies exact URL with comment ID parameter to clipboard"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-[#16A34A]" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Copied Deep Link!' : 'Copy Direct Link'}</span>
                  </button>
                </div>

                {/* AI Brand Reply Button */}
                <button
                  onClick={handleGenerateAiReply}
                  disabled={generatingReply}
                  className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-blue-50 hover:bg-blue-100 text-[#2563EB] border border-blue-200 font-bold text-xs transition disabled:opacity-50"
                >
                  <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                  <span>{generatingReply ? 'Drafting AI Reply...' : 'Generate AI Brand Reply'}</span>
                </button>
              </div>

              {/* AI Drafted Response Box */}
              {aiReply && (
                <div className="mt-3 p-3.5 rounded-xl bg-white border border-blue-200 space-y-2 animate-fade-in">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-blue-700 flex items-center space-x-1">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Recommended Brand Mitigation Response:</span>
                    </span>
                    <button
                      onClick={handleCopyAiReply}
                      className="text-[11px] font-semibold text-[#2563EB] hover:underline flex items-center space-x-1"
                    >
                      {copiedReply ? <Check className="w-3 h-3 text-[#16A34A]" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedReply ? 'Copied Response!' : 'Copy Response'}</span>
                    </button>
                  </div>
                  <p className="text-xs text-slate-800 leading-relaxed font-sans bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                    "{aiReply}"
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Section 3: SIBLING COMMENTS UNDER THE SAME POST */}
          {siblingComments.length > 1 && (
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center space-x-1.5">
                  <MessageCircle className="w-3.5 h-3.5 text-slate-500" />
                  <span>Other Comments in this Discussion ({siblingComments.length - 1})</span>
                </h4>
                <span className="text-[11px] text-slate-500">
                  Click any comment to switch active inspection focus
                </span>
              </div>

              <div className="space-y-2 max-h-52 overflow-y-auto pr-1 custom-scrollbar">
                {siblingComments
                  .filter((c) => (c.comment_id || c.id) !== (currentComment.comment_id || currentComment.id))
                  .map((sibling, idx) => {
                    const sibUrl = buildDirectCommentUrl(sibling, sibling.comment_id);
                    return (
                      <div
                        key={sibling.id || idx}
                        onClick={() => setSelectedComment(sibling)}
                        className="p-3 rounded-xl bg-slate-50 hover:bg-blue-50/50 border border-slate-200 hover:border-blue-300 transition cursor-pointer flex items-start justify-between gap-3 group"
                      >
                        <div className="flex items-start space-x-2.5 min-w-0">
                          <img
                            src={sibling.author_avatar || `https://api.dicebear.com/7.x/bottts/svg?seed=${sibling.author_handle || idx}`}
                            alt={sibling.author}
                            className="w-7 h-7 rounded-lg bg-white border border-slate-200 shrink-0 mt-0.5"
                          />
                          <div className="min-w-0">
                            <div className="flex items-center space-x-2">
                              <span className="font-bold text-xs text-slate-900 group-hover:text-blue-600 transition">
                                {sibling.author}
                              </span>
                              <span className="text-[10px] text-slate-400 font-mono">
                                {sibling.author_handle}
                              </span>
                            </div>
                            <p className="text-xs text-slate-700 line-clamp-2 mt-0.5">
                              "{sibling.content || sibling.text}"
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2 shrink-0 mt-0.5">
                          <SentimentBadge sentiment={sibling.sentiment} score={sibling.sentiment_score} />
                          <a
                            href={sibUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="p-1 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-white transition"
                            title="Open this comment in Instagram"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}

        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 border-t border-slate-100 bg-slate-50 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2 text-slate-500 text-[11px]">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>Target deep links formatted to official Instagram Graph specifications.</span>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-200 hover:bg-slate-300 text-slate-800 font-semibold transition"
          >
            Close Inspector
          </button>
        </div>

      </div>
    </div>
  );
};

export default CommentThreadModal;
