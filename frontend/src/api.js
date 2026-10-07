/**
 * e-SewaSathi API Client
 * Connects frontend to the FastAPI backend with token caching and error handling.
 */

const BASE_URL = '/api';

export function getToken() {
  return localStorage.getItem('esewa_token') || '';
}

export function setToken(token) {
  if (token) {
    localStorage.setItem('esewa_token', token);
  } else {
    localStorage.removeItem('esewa_token');
  }
}

export function getCurrentUser() {
  const user = localStorage.getItem('esewa_user');
  try {
    return user ? JSON.parse(user) : null;
  } catch {
    return null;
  }
}

export function setCurrentUser(user) {
  if (user) {
    localStorage.setItem('esewa_user', JSON.stringify(user));
  } else {
    localStorage.removeItem('esewa_user');
  }
}

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const headers = { ...options.headers };
  const token = getToken();

  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401 && !path.includes('/auth/login')) {
    // Session expired or invalid
    setToken(null);
    setCurrentUser(null);
  }

  let data = null;
  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    data = await res.json();
  } else if (!res.ok) {
    data = { detail: await res.text() };
  }

  if (!res.ok) {
    const errorMsg = data?.detail || data?.message || `HTTP error ${res.status}`;
    const error = new Error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
    error.status = res.status;
    error.data = data;
    throw error;
  }

  return data;
}

export const api = {
  // System Health
  async getHealth() {
    return request('/health');
  },

  // Auth
  async register(payload) {
    return request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async login(email, password) {
    const data = await request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    setToken(data.access_token);
    setCurrentUser(data.user);
    return data;
  },

  async logout() {
    try {
      await request('/auth/logout', { method: 'POST' });
    } catch (e) {
      console.warn('Logout API warning:', e);
    } finally {
      setToken(null);
      setCurrentUser(null);
    }
  },

  async getMe() {
    const user = await request('/users/me');
    setCurrentUser(user);
    return user;
  },

  // Applications
  async listApplications() {
    return request('/applications');
  },

  async getApplication(id) {
    return request(`/applications/${id}`);
  },

  async createApplication(payload) {
    return request('/applications', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateApplication(id, payload) {
    return request(`/applications/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  async cancelApplication(id) {
    return request(`/applications/${id}`, {
      method: 'DELETE',
    });
  },

  // Documents
  async listApplicationDocuments(applicationId) {
    return request(`/applications/${applicationId}/documents`);
  },

  async uploadDocument(applicationId, documentType, file) {
    const formData = new FormData();
    formData.append('document_type', documentType);
    formData.append('file', file);

    return request(`/applications/${applicationId}/documents`, {
      method: 'POST',
      body: formData,
    });
  },

  async deleteDocument(documentId) {
    return request(`/documents/${documentId}`, {
      method: 'DELETE',
    });
  },

  getDocumentDownloadUrl(documentId) {
    return `${BASE_URL}/documents/${documentId}/download`;
  },
};
