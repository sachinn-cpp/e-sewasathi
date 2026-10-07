import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import DashboardView from './components/DashboardView';
import ApplicationsListView from './components/ApplicationsListView';
import DocumentsLockerView from './components/DocumentsLockerView';
import AuthModal from './components/AuthModal';
import NewApplicationModal from './components/NewApplicationModal';
import ApplicationDetailModal from './components/ApplicationDetailModal';
import { api, getCurrentUser } from './api';

export default function App() {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [user, setUser] = useState(getCurrentUser());
  const [health, setHealth] = useState(null);
  const [applications, setApplications] = useState([]);
  const [loadingApps, setLoadingApps] = useState(false);

  // Modals
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [newAppModalOpen, setNewAppModalOpen] = useState(false);
  const [selectedApp, setSelectedApp] = useState(null);

  // Initial check
  useEffect(() => {
    checkHealth();
    if (user) {
      loadApplications();
    }
  }, []);

  async function checkHealth() {
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch (e) {
      console.warn('Backend offline or connecting...', e);
      setHealth(null);
    }
  }

  async function loadApplications() {
    setLoadingApps(true);
    try {
      const list = await api.listApplications();
      setApplications(list);
    } catch (err) {
      console.error('Error fetching applications:', err);
    } finally {
      setLoadingApps(false);
    }
  }

  function handleAuthSuccess() {
    setUser(getCurrentUser());
    loadApplications();
  }

  async function handleLogout() {
    await api.logout();
    setUser(null);
    setApplications([]);
    setSelectedApp(null);
    setCurrentTab('dashboard');
  }

  function handleApplicationCreated(newApp) {
    setApplications((prev) => [newApp, ...prev]);
    setSelectedApp(newApp);
  }

  return (
    <div className="app-container">
      {/* Navigation Header */}
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        user={user}
        onOpenAuth={() => setAuthModalOpen(true)}
        onLogout={handleLogout}
        onNewApp={() => setNewAppModalOpen(true)}
        health={health}
      />

      {/* Main Tab Views */}
      <main>
        {currentTab === 'dashboard' && (
          <DashboardView
            applications={applications}
            user={user}
            onOpenNewApp={() => setNewAppModalOpen(true)}
            onOpenAuth={() => setAuthModalOpen(true)}
            onSelectApp={(app) => setSelectedApp(app)}
            setCurrentTab={setCurrentTab}
          />
        )}

        {currentTab === 'applications' && (
          <ApplicationsListView
            applications={applications}
            user={user}
            onSelectApp={(app) => setSelectedApp(app)}
            onOpenNewApp={() => setNewAppModalOpen(true)}
            onOpenAuth={() => setAuthModalOpen(true)}
          />
        )}

        {currentTab === 'documents' && (
          <DocumentsLockerView
            applications={applications}
            onSelectApp={(app) => setSelectedApp(app)}
          />
        )}
      </main>

      {/* Modals */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
      />

      <NewApplicationModal
        isOpen={newAppModalOpen}
        onClose={() => setNewAppModalOpen(false)}
        onCreated={handleApplicationCreated}
      />

      <ApplicationDetailModal
        application={selectedApp}
        isOpen={!!selectedApp}
        onClose={() => setSelectedApp(null)}
        onRefresh={loadApplications}
      />
    </div>
  );
}
