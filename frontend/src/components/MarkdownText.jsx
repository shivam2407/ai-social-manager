export default function MarkdownText({ text }) {
  if (!text) return null;

  // Split into lines and group into blocks
  const lines = text.split("\n");
  const blocks = [];
  let current = [];

  const flushParagraph = () => {
    if (current.length > 0) {
      blocks.push({ type: "p", content: current.join(" ") });
      current = [];
    }
  };

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) {
      flushParagraph();
      continue;
    }
    if (/^\d+\.\s/.test(line) || /^[-*]\s/.test(line)) {
      flushParagraph();
      blocks.push({ type: "li", content: line.replace(/^(\d+\.\s|[-*]\s)/, "") });
    } else {
      current.push(line);
    }
  }
  flushParagraph();

  // Merge consecutive li blocks into ul groups
  const merged = [];
  for (const block of blocks) {
    if (block.type === "li") {
      const prev = merged[merged.length - 1];
      if (prev && prev.type === "ul") {
        prev.items.push(block.content);
      } else {
        merged.push({ type: "ul", items: [block.content] });
      }
    } else {
      merged.push(block);
    }
  }

  // Inline formatting: **bold**
  const formatInline = (str) => {
    const parts = [];
    const regex = /\*\*(.+?)\*\*/g;
    let last = 0;
    let match;
    while ((match = regex.exec(str)) !== null) {
      if (match.index > last) parts.push(str.slice(last, match.index));
      parts.push(
        <strong key={match.index} className="text-white font-semibold">
          {match[1]}
        </strong>,
      );
      last = regex.lastIndex;
    }
    if (last < str.length) parts.push(str.slice(last));
    return parts;
  };

  return merged.map((block, i) => {
    if (block.type === "p") {
      return (
        <p key={i} className="mb-2 last:mb-0">
          {formatInline(block.content)}
        </p>
      );
    }
    if (block.type === "ul") {
      return (
        <ul
          key={i}
          className="list-disc list-inside mb-2 last:mb-0 space-y-1 ml-1"
        >
          {block.items.map((item, j) => (
            <li key={j}>{formatInline(item)}</li>
          ))}
        </ul>
      );
    }
    return null;
  });
}
