// Layout component with sidebar and main content area
import { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useBackgroundTheme, useSidebarCollapsed } from '../store/useStore';

export default function Layout() {
  const sidebarCollapsed = useSidebarCollapsed();
  const backgroundTheme = useBackgroundTheme();

  useEffect(() => {
    document.documentElement.setAttribute('data-bg-theme', backgroundTheme);
  }, [backgroundTheme]);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main
        className={`flex-1 transition-all duration-300 ${
          sidebarCollapsed ? 'ml-16' : 'ml-72'
        }`}
      >
        <div className="p-6 max-w-[1800px] mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
