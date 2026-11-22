import React from 'react';

interface ChipProps {
  children: React.ReactNode;
  tone?: 'violet' | 'teal' | 'warning';
  onClick?: () => void;
}

export const Chip: React.FC<ChipProps> = ({ children, tone = 'violet', onClick }) => {
  const border =
    tone === 'teal'
      ? 'border-[#2EC4B6]/60 text-[#2EC4B6]'
      : tone === 'warning'
        ? 'border-amber-400/70 text-amber-300'
        : 'border-[#6C63FF]/60';
  const Tag = onClick ? 'button' : 'span';
  return (
    <Tag
      onClick={onClick}
      className={`glass inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition hover:border-[#6C63FF] ${border}`}
    >
      {children}
    </Tag>
  );
};
