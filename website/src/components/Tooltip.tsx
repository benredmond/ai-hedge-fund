interface TooltipProps {
  text: string;
  children: React.ReactNode;
  align?: 'center' | 'right';
}

export function Tooltip({ text, children, align = 'center' }: TooltipProps) {
  const positionClasses = align === 'right'
    ? 'right-0'
    : 'left-1/2 -translate-x-1/2';

  return (
    <span className="group relative inline-flex items-center">
      {children}
      <span className={`invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-opacity
                       absolute ${positionClasses} top-full mt-1.5
                       px-2 py-1 bg-foreground text-background text-xs font-sans
                       rounded whitespace-nowrap z-10 pointer-events-none`}>
        {text}
      </span>
    </span>
  );
}
