import React from 'react';

interface GlassButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
}

export const GlassButton: React.FC<GlassButtonProps> = ({
  variant = 'primary',
  className = '',
  children,
  ...rest
}) => {
  const styles =
    variant === 'primary'
      ? 'bg-gradient-to-r from-[#2EC4B6] via-[#4F8CFF] to-[#6C63FF] text-[#F8FAFC] font-semibold border border-white/25 shadow-[0_6px_22px_rgba(108,99,255,0.34)] hover:brightness-110 disabled:opacity-50'
      : variant === 'secondary'
        ? 'glass border border-[#6C63FF]/60 hover:bg-[#6C63FF]/15'
        : 'hover:bg-white/10';
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm transition ${styles} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
};
