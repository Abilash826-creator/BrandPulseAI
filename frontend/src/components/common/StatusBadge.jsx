import React from 'react';
import { 
  Smile, 
  Meh, 
  Frown, 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  Twitter, 
  MessageSquare, 
  Linkedin, 
  Newspaper, 
  Star,
  Instagram,
  HelpCircle,
  ShoppingBag,
  Sparkles,
  Info
} from 'lucide-react';

export const SentimentBadge = ({ sentiment, score }) => {
  const s = sentiment?.toLowerCase();
  if (s === 'positive') {
    return (
      <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-[#16A34A] border border-emerald-200">
        <Smile className="w-3.5 h-3.5" />
        <span>Positive</span>
        {score !== undefined && <span className="opacity-80 text-[10px]">({score > 0 ? `+${score}` : score})</span>}
      </span>
    );
  }
  if (s === 'negative') {
    return (
      <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-50 text-[#DC2626] border border-red-200">
        <Frown className="w-3.5 h-3.5" />
        <span>Negative</span>
        {score !== undefined && <span className="opacity-80 text-[10px]">({score})</span>}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-[#64748B] border border-slate-200">
      <Meh className="w-3.5 h-3.5" />
      <span>Neutral</span>
      {score !== undefined && <span className="opacity-80 text-[10px]">({score})</span>}
    </span>
  );
};

export const SeverityBadge = ({ severity }) => {
  const sev = severity?.toLowerCase();
  if (sev === 'critical') {
    return (
      <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-bold bg-red-50 text-[#DC2626] border border-red-200">
        <ShieldAlert className="w-3.5 h-3.5" />
        <span className="tracking-wide uppercase">Critical Crisis</span>
      </span>
    );
  }
  if (sev === 'warning' || sev === 'high') {
    return (
      <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-bold bg-orange-50 text-[#F97316] border border-orange-200">
        <AlertTriangle className="w-3.5 h-3.5" />
        <span className="tracking-wide uppercase">Warning</span>
      </span>
    );
  }
  if (sev === 'medium' || sev === 'low_alert') {
    return (
      <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-bold bg-yellow-50 text-[#CA8A04] border border-yellow-200">
        <AlertTriangle className="w-3.5 h-3.5" />
        <span className="tracking-wide uppercase">Low Alert</span>
      </span>
    );
  }
  return (
    <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-50 text-[#16A34A] border border-emerald-200">
      <CheckCircle2 className="w-3.5 h-3.5" />
      <span className="tracking-wide uppercase">Healthy / Normal</span>
    </span>
  );
};

export const IntentBadge = ({ intent }) => {
  const config = {
    complaint: { label: 'Issue / Complaint', color: 'bg-red-50 text-[#DC2626] border-red-200', icon: Frown },
    query: { label: 'Product Query', color: 'bg-blue-50 text-[#2563EB] border-blue-200', icon: HelpCircle },
    purchase_intent: { label: 'Purchase Intent', color: 'bg-purple-50 text-[#7C3AED] border-purple-200', icon: ShoppingBag },
    praise: { label: 'Praise & Win', color: 'bg-emerald-50 text-[#16A34A] border-emerald-200', icon: Sparkles },
    general: { label: 'General Talk', color: 'bg-slate-100 text-slate-600 border-slate-200', icon: MessageSquare },
  };

  const item = config[intent?.toLowerCase()] || config.general;
  const Icon = item.icon;

  return (
    <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-md text-[11px] font-semibold border ${item.color}`}>
      <Icon className="w-3 h-3" />
      <span>{item.label}</span>
    </span>
  );
};

export const PlatformBadge = ({ platform }) => {
  const p = platform?.toLowerCase() || '';
  const config = {
    google: { label: 'Google Review', color: 'text-blue-700 bg-blue-50 border-blue-200', icon: Star },
    'google reviews': { label: 'Google Review', color: 'text-blue-700 bg-blue-50 border-blue-200', icon: Star },
    google_reviews: { label: 'Google Review', color: 'text-blue-700 bg-blue-50 border-blue-200', icon: Star },
    facebook: { label: 'Facebook', color: 'text-indigo-700 bg-indigo-50 border-indigo-200', icon: MessageSquare },
    'facebook reviews': { label: 'Facebook Review', color: 'text-indigo-700 bg-indigo-50 border-indigo-200', icon: MessageSquare },
    instagram: { label: 'Instagram', color: 'text-rose-700 bg-rose-50 border-rose-200', icon: Instagram },
    pasted: { label: 'Pasted Review', color: 'text-emerald-700 bg-emerald-50 border-emerald-200', icon: MessageSquare },
    'pasted text': { label: 'Pasted Review', color: 'text-emerald-700 bg-emerald-50 border-emerald-200', icon: MessageSquare },
    twitter: { label: 'X / Twitter', color: 'text-slate-800 bg-slate-100 border-slate-200', icon: Twitter },
    reddit: { label: 'Reddit', color: 'text-orange-700 bg-orange-50 border-orange-200', icon: MessageSquare },
    linkedin: { label: 'LinkedIn', color: 'text-blue-700 bg-blue-50 border-blue-200', icon: Linkedin },
    news: { label: 'Tech News', color: 'text-purple-700 bg-purple-50 border-purple-200', icon: Newspaper },
    review: { label: 'Trustpilot', color: 'text-emerald-700 bg-emerald-50 border-emerald-200', icon: Star },
  };

  const matchedKey = Object.keys(config).find(k => p.includes(k));
  const item = matchedKey ? config[matchedKey] : { label: platform || 'Review', color: 'text-slate-700 bg-slate-100 border-slate-200', icon: Star };
  const Icon = item.icon;

  return (
    <span className={`inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-lg text-xs font-semibold border ${item.color}`}>
      <Icon className="w-3.5 h-3.5" />
      <span>{item.label}</span>
    </span>
  );
};

