import { Twitter, Linkedin, Instagram } from "lucide-react";

const config = {
  twitter: {
    icon: Twitter,
    label: "Twitter",
    bg: "bg-sky-500/15",
    text: "text-sky-400",
    border: "border-sky-500/30",
  },
  linkedin: {
    icon: Linkedin,
    label: "LinkedIn",
    bg: "bg-blue-500/15",
    text: "text-blue-400",
    border: "border-blue-500/30",
  },
  instagram: {
    icon: Instagram,
    label: "Instagram",
    bg: "bg-pink-500/15",
    text: "text-pink-400",
    border: "border-pink-500/30",
  },
};

export default function PlatformBadge({ platform }) {
  const c = config[platform] || config.twitter;
  const Icon = c.icon;
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${c.bg} ${c.text} ${c.border}`}
    >
      <Icon className="w-3 h-3" />
      {c.label}
    </span>
  );
}
