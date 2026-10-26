import React, { useState } from 'react';
import { PlatformBadge, SentimentBadge, IntentBadge } from '../common/StatusBadge';
import CommentThreadModal, { buildDirectCommentUrl } from './CommentThreadModal';
import { monitoringAPI } from '../../services/api';
import { 
  Flame, 
  ExternalLink, 
  Clock, 
  Users, 
  Video, 
  FileText, 
  ChevronDown, 
  ChevronUp, 
  CheckCircle2, 
  AlertTriangle,
  Package,
  Layers,
  Sparkles,
  Volume2,
  VolumeX,
  Instagram,
  MessageSquare,
  ArrowUpRight,
  Eye,
  MessageCircle,
  Star,
  CornerDownRight,
  Copy,
  Send,
  Loader2,
  Languages
} from 'lucide-react';

const getLanguageLabel = (lang) => {
  if (!lang) return null;
  const l = lang.toLowerCase();
  if (l === 'ta') return 'தமிழ் (Tamil)';
  if (l === 'tanglish') return 'Tanglish';
  if (l === 'hi') return 'हिंदी (Hindi)';
  if (l === 'hinglish') return 'Hinglish';
  if (l === 'en') return 'English';
  return l.toUpperCase();
};

const FeedStream = ({ mentions = [], maxItems = 10, showViewAll = true, onViewAll, onReplySuccess }) => {
  const [expandedTranscripts, setExpandedTranscripts] = useState({});
  const [showTranslations, setShowTranslations] = useState({});
  const [inspectorItem, setInspectorItem] = useState(null);
  const [activeReplyId, setActiveReplyId] = useState(null);
  const [replyDrafts, setReplyDrafts] = useState({});
  const [replyLoading, setReplyLoading] = useState({});
  const [copiedId, setCopiedId] = useState(null);
  const [localReplies, setLocalReplies] = useState({});

  const toggleTranslation = (id) => {
    setShowTranslations(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const toggleTranscript = (id) => {
    setExpandedTranscripts(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const toggleReplyBox = (id, existingReply = '') => {
    setActiveReplyId(prev => (prev === id ? null : id));
    if (!replyDrafts[id]) {
      setReplyDrafts(prev => ({ ...prev, [id]: existingReply || '' }));
    }
  };

  const handleTemplateClick = (id, text) => {
    setReplyDrafts(prev => ({ ...prev, [id]: text }));
  };

  const handleSendReply = async (mentionId) => {
    const text = replyDrafts[mentionId]?.trim();
    if (!text) return;
    setReplyLoading(prev => ({ ...prev, [mentionId]: true }));
    try {
      await monitoringAPI.replyToMention(mentionId, text);
      setLocalReplies(prev => ({
        ...prev,
        [mentionId]: {
          replied: true,
          reply_text: text,
          reply_timestamp: new Date().toISOString()
        }
      }));
      setActiveReplyId(null);
      if (onReplySuccess) onReplySuccess(mentionId, text);
    } catch (err) {
      console.error('Failed to post reply:', err);
    } finally {
      setReplyLoading(prev => ({ ...prev, [mentionId]: false }));
    }
  };

  const handleCopyReply = (mentionId) => {
    const text = replyDrafts[mentionId]?.trim();
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedId(mentionId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const displayMentions = mentions.slice(0, maxItems);

  if (!displayMentions || displayMentions.length === 0) {
    return (
      <div className="p-8 text-center bg-white border border-slate-200 rounded-2xl text-slate-500 text-xs shadow-sm">
        No reviews or customer mentions recorded yet. Sync Google Reviews, paste customer feedback, or connect your social accounts.
      </div>
    );
  }

  return (
    <div className="space-y-3.5">
      {displayMentions.map((item) => {
        const isViral = item.virality_score > 70;
        const timeAgo = formatTime(item.timestamp);
        const isInstagram = item.platform?.toLowerCase() === 'instagram';
        const isGoogle = item.platform?.toLowerCase().includes('google') || item.source?.toLowerCase().includes('google');
        const isReel = item.media_type === 'REEL' || item.media_type === 'VIDEO';
        const isComment = item.media_type === 'COMMENT' || Boolean(item.comment_id);
        const hasTranscript = Boolean(item.transcript);
        const isTranscriptOpen = Boolean(expandedTranscripts[item.id]);
        const relevance = item.relevance_score !== undefined ? item.relevance_score : 0.85;
        const directTargetUrl = buildDirectCommentUrl(item, item.comment_id);

        const localReply = localReplies[item.id];
        const isReplied = localReply ? localReply.replied : Boolean(item.replied);
        const replyText = localReply ? localReply.reply_text : item.reply_text;
        const replyTime = localReply ? localReply.reply_timestamp : item.reply_timestamp;
        const isReplyOpen = activeReplyId === item.id;

        return (
          <div
            key={item.id}
            className={`p-4 rounded-2xl bg-white border transition-all shadow-sm group ${
              item.is_crisis_flag 
                ? 'border-red-300 bg-red-50/40 border-l-4 border-l-[#DC2626]' 
                : isGoogle
                  ? 'border-slate-200 hover:border-blue-300 hover:shadow-md'
                  : 'border-slate-200 hover:border-slate-300 hover:shadow-md'
            }`}
          >
            {/* Header: Author Info + Platform + Rating + Sentiment */}
            <div className="flex items-start justify-between gap-2 flex-wrap sm:flex-nowrap">
              <div className="flex items-center space-x-3 min-w-0">
                <button
                  type="button"
                  onClick={() => setInspectorItem(item)}
                  className="shrink-0 focus:outline-none"
                  title="Inspect customer mention"
                >
                  <img
                    src={item.author_avatar || `https://api.dicebear.com/7.x/bottts/svg?seed=${item.author_handle || item.author}`}
                    alt={item.author}
                    className="w-9 h-9 rounded-xl bg-slate-100 border border-slate-200 object-cover hover:opacity-90 hover:ring-2 hover:ring-blue-400 transition"
                  />
                </button>
                <div className="min-w-0">
                  <div className="flex items-center space-x-2 flex-wrap">
                    <button
                      type="button"
                      onClick={() => setInspectorItem(item)}
                      className="font-bold text-xs text-slate-900 hover:text-[#2563EB] truncate flex items-center space-x-1 text-left"
                      title="Click to inspect review"
                    >
                      <span>{item.author}</span>
                    </button>
                    <span className="text-[11px] text-slate-500 font-mono truncate">{item.author_handle}</span>

                    {/* Star Rating Badge */}
                    {item.rating && (
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-amber-50 text-amber-700 border border-amber-200 text-[10px] font-bold">
                        <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                        <span>{item.rating}.0</span>
                      </span>
                    )}

                    {/* Replied / Needs Reply Status Pill */}
                    {isReplied ? (
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-emerald-50 text-[#16A34A] border border-emerald-200 text-[10px] font-semibold">
                        <CheckCircle2 className="w-3 h-3 text-[#16A34A]" />
                        <span>Replied</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200 text-[10px] font-semibold">
                        <span>Needs Reply</span>
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-2 text-[10px] text-slate-400 mt-0.5">
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{timeAgo}</span>
                    </span>
                    {item.language && (
                      <>
                        <span>•</span>
                        <span className="inline-flex items-center space-x-1 font-semibold text-[10px] text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">
                          <Languages className="w-3 h-3 text-slate-500" />
                          <span>{getLanguageLabel(item.language)}</span>
                        </span>
                      </>
                    )}
                    {item.translated_text && item.language && item.language !== 'en' && (
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); toggleTranslation(item.id); }}
                        className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 border border-blue-200 transition"
                      >
                        <span>{showTranslations[item.id] ? 'Show Original' : 'Translate'}</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2 shrink-0">
                <PlatformBadge platform={item.source || item.platform} />
                <SentimentBadge sentiment={item.sentiment} score={item.sentiment_score} />
              </div>
            </div>

            {/* Clickable Content Body */}
            <div className="mt-3">
              <div
                onClick={() => setInspectorItem(item)}
                className="block text-xs text-slate-800 hover:text-[#2563EB] leading-relaxed font-normal group-hover:text-blue-950 transition cursor-pointer"
              >
                {showTranslations[item.id] && item.translated_text ? (
                  <div className="p-3 rounded-xl bg-blue-50/60 border border-blue-200 space-y-1">
                    <div className="flex items-center justify-between text-[11px] text-blue-700 font-semibold">
                      <span className="flex items-center space-x-1">
                        <Languages className="w-3.5 h-3.5" />
                        <span>English Translation:</span>
                      </span>
                      <span className="text-[10px] text-blue-500 font-normal">Original: {getLanguageLabel(item.language)}</span>
                    </div>
                    <p className="text-slate-900 font-medium text-xs leading-relaxed">"{item.translated_text}"</p>
                    <p className="text-slate-500 text-[11px] italic pt-1 border-t border-blue-100">Original: "{item.original_text || item.content}"</p>
                  </div>
                ) : (
                  item.content
                )}
              </div>
            </div>

            {/* Topics & Preset Aspects */}
            {((item.topics && item.topics.length > 0) || (item.detected_products && item.detected_products.length > 0) || (item.aspects && item.aspects.length > 0) || item.product_detected) && (
              <div className="mt-2.5 flex items-center flex-wrap gap-1.5 pt-1">
                {(item.topics || []).map((t, idx) => (
                  <span key={`topic-${idx}`} className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 border border-purple-200 text-[10px] font-semibold">
                    <span>#{t}</span>
                  </span>
                ))}
                {item.product_detected && (
                  <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-blue-50 text-[#2563EB] border border-blue-200 text-[10px] font-semibold">
                    <Package className="w-3 h-3" />
                    <span>Item: {item.product_detected}</span>
                  </span>
                )}

                {(item.aspects || []).map((asp, idx) => {
                  const aspSent = asp.sentiment?.toLowerCase();
                  const colorCls = aspSent === 'positive'
                    ? 'bg-emerald-50 text-[#16A34A] border-emerald-200'
                    : aspSent === 'negative'
                      ? 'bg-red-50 text-[#DC2626] border-red-200'
                      : 'bg-slate-100 text-slate-600 border-slate-200';

                  return (
                    <span 
                      key={idx}
                      className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-md text-[10px] font-medium border ${colorCls}`}
                    >
                      <span className="capitalize">{asp.aspect?.replace('_', ' ')}:</span>
                      <strong className="capitalize">{aspSent}</strong>
                    </span>
                  );
                })}
              </div>
            )}

            {/* Existing Owner Reply Bubble */}
            {replyText && (
              <div className="mt-3 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                <div className="flex items-center justify-between text-[11px] text-slate-500 mb-1">
                  <span className="font-semibold text-slate-800 flex items-center space-x-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#16A34A]" />
                    <span>Your Response:</span>
                  </span>
                  <span>{formatTime(replyTime)}</span>
                </div>
                <p className="text-slate-700 italic">"{replyText}"</p>
              </div>
            )}

            {/* Inline Reply Composer Form */}
            {isReplyOpen && (
              <div className="mt-3 p-3.5 rounded-xl bg-blue-50/50 border border-blue-200 space-y-2.5 animate-fade-in">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800 flex items-center space-x-1.5">
                    <CornerDownRight className="w-3.5 h-3.5 text-blue-600" />
                    <span>Reply to {item.author}</span>
                  </span>
                  <div className="flex items-center space-x-1">
                    <button
                      type="button"
                      onClick={() => handleTemplateClick(item.id, "Thank you so much for your kind words! We look forward to serving you again soon.")}
                      className="text-[10px] px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-600 hover:border-blue-400 hover:text-blue-600"
                    >
                      + Thank You
                    </button>
                    <button
                      type="button"
                      onClick={() => handleTemplateClick(item.id, "We are truly sorry for the inconvenience. Please share your contact details so our manager can assist you directly.")}
                      className="text-[10px] px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-600 hover:border-blue-400 hover:text-blue-600"
                    >
                      + Apology
                    </button>
                  </div>
                </div>

                <textarea
                  rows={3}
                  value={replyDrafts[item.id] || ''}
                  onChange={(e) => setReplyDrafts(prev => ({ ...prev, [item.id]: e.target.value }))}
                  placeholder={`Write your polite reply to ${item.author}...`}
                  className="w-full text-xs p-2.5 bg-white border border-slate-300 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600"
                />

                <div className="flex items-center justify-end space-x-2">
                  <button
                    type="button"
                    onClick={() => handleCopyReply(item.id)}
                    className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 text-xs font-semibold flex items-center space-x-1 shadow-2xs"
                  >
                    <Copy className="w-3.5 h-3.5 text-slate-500" />
                    <span>{copiedId === item.id ? 'Copied!' : 'Copy Text'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleSendReply(item.id)}
                    disabled={replyLoading[item.id] || !replyDrafts[item.id]?.trim()}
                    className="px-3.5 py-1.5 rounded-lg bg-[#2563EB] hover:bg-[#1E3A8A] text-white text-xs font-semibold flex items-center space-x-1.5 disabled:opacity-50 shadow-2xs"
                  >
                    {replyLoading[item.id] ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Send className="w-3.5 h-3.5" />
                    )}
                    <span>{isReplied ? 'Update Reply' : 'Send Reply'}</span>
                  </button>
                </div>
              </div>
            )}

            {/* Footer Actions */}
            <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between flex-wrap gap-2 text-xs">
              <div className="flex items-center space-x-2">
                <IntentBadge intent={item.intent} />
              </div>

              <div className="flex items-center space-x-2">
                {/* Reply to Review Button */}
                <button
                  type="button"
                  onClick={() => toggleReplyBox(item.id, replyText)}
                  className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition shadow-2xs ${
                    isReplyOpen
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-blue-50 hover:bg-blue-100 text-[#2563EB] border-blue-200'
                  }`}
                >
                  <MessageSquare className="w-3.5 h-3.5" />
                  <span>{isReplied ? 'Edit Reply' : 'Reply to Customer'}</span>
                </button>

                {/* Inspect Thread Trigger */}
                <button
                  type="button"
                  onClick={() => setInspectorItem(item)}
                  className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition shadow-2xs"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Inspect</span>
                </button>
              </div>
            </div>
          </div>
        );
      })}

      {showViewAll && onViewAll && (
        <button
          onClick={onViewAll}
          className="w-full py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-[#2563EB] hover:text-[#1E3A8A] text-xs font-semibold transition shadow-sm"
        >
          View All Monitored Mentions ({mentions.length})
        </button>
      )}

      {/* Interactive Post & Comment Thread Inspector Modal */}
      <CommentThreadModal
        isOpen={Boolean(inspectorItem)}
        onClose={() => setInspectorItem(null)}
        activeItem={inspectorItem}
        allMentions={mentions}
      />
    </div>
  );
};

function formatTime(timestamp) {
  if (!timestamp) return 'just now';
  try {
    const diff = Math.floor((new Date() - new Date(timestamp)) / 1000);
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  } catch (e) {
    return 'recently';
  }
}

export default FeedStream;
