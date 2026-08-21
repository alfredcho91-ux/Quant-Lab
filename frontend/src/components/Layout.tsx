// Layout component with sidebar and main content area
import { useEffect, type ReactNode } from 'react';
import Sidebar from './Sidebar';
import { useBackgroundTheme, useSidebarCollapsed } from '../store/useStore';
import { useMediaQuery } from '../hooks/useMediaQuery';

export default function Layout({ children }: { children: ReactNode }) {
  const sidebarCollapsed = useSidebarCollapsed();
  const isMobile = useMediaQuery('(max-width: 767px)');
  const backgroundTheme = useBackgroundTheme();
  const isSidebarCollapsed = sidebarCollapsed || isMobile;

  useEffect(() => {
    document.documentElement.setAttribute('data-bg-theme', backgroundTheme);
  }, [backgroundTheme]);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main
        className={`min-w-0 flex-1 transition-all duration-300 ${
          isSidebarCollapsed ? 'ml-16' : 'ml-72'
        }`}
      >
        <div className="mx-auto min-w-0 max-w-[1800px] p-3 sm:p-6">
          {children}
        </div>
      </main>
    </div>
  );
}
