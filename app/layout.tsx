import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'TTS Reader',
  description: 'Text to Speech Reader',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-gray-100 antialiased overflow-hidden">
        {children}
      </body>
    </html>
  );
}
