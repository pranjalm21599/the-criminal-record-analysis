import Sidebar from './Sidebar';

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-base-bg">
      <Sidebar />
      <main className="ml-60 px-8 py-7">
        {children}
      </main>
    </div>
  );
}
