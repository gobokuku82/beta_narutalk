/**
 * cn() — clsx + tailwind-merge 통합. className 병합 헬퍼.
 *
 * spec: 61 §4.6
 *
 * 사용 예:
 *   <button className={cn(
 *     'px-4 py-2 rounded-sm',
 *     variant === 'primary' && 'bg-primary',
 *     className,
 *   )} />
 */
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
