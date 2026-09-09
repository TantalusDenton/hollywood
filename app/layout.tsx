import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Hollywood — AI Film Studio',
  description: 'An agentic movie-generation pipeline for directors.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
