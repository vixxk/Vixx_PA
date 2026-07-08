export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const getFileUrl = (fileUrl) => {
  if (!fileUrl) return '';
  let url = fileUrl;
  if (url.includes('localhost:8000')) {
    const base = API_BASE_URL.replace(/\/api\/v1\/?$/, '');
    url = url.replace('http://localhost:8000', base);
  }
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  const base = API_BASE_URL.replace(/\/api\/v1\/?$/, '');
  return `${base}${url}`;
};

const getHeaders = () => {
  const token = localStorage.getItem('token');
  const googleToken = localStorage.getItem('google_token');
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  if (googleToken) {
    headers['X-Google-Token'] = googleToken;
  }
  return headers;
};

const handleResponse = async (response) => {
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || 'Something went wrong');
  }
  if (response.status === 204) return null;
  return response.json();
};

export const api = {
  auth: {
    register: async (name, email, password) => {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ name, email, password }),
      });
      return handleResponse(response);
    },
    login: async (username, password) => {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
      });
      const data = await handleResponse(response);
      if (data && data.access_token) {
        localStorage.setItem('token', data.access_token);
      }
      return data;
    },
    me: async () => {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        method: 'GET',
        headers: getHeaders(),
      });
      return handleResponse(response);
    },
    logout: () => {
      localStorage.removeItem('token');
    },
    isAuthenticated: () => {
      return !!localStorage.getItem('token');
    }
  },

  projects: {
    list: async () => {
      const response = await fetch(`${API_BASE_URL}/projects/`, {
        method: 'GET',
        headers: getHeaders(),
      });
      return handleResponse(response);
    },
    create: async (projectData) => {
      const response = await fetch(`${API_BASE_URL}/projects/`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(projectData),
      });
      return handleResponse(response);
    },
    get: async (id) => {
      const response = await fetch(`${API_BASE_URL}/projects/${id}`, {
        method: 'GET',
        headers: getHeaders(),
      });
      return handleResponse(response);
    },
    update: async (id, projectData) => {
      const response = await fetch(`${API_BASE_URL}/projects/${id}`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify(projectData),
      });
      return handleResponse(response);
    },
    delete: async (id) => {
      const response = await fetch(`${API_BASE_URL}/projects/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
      });
      return handleResponse(response);
    }
  },

  todos: {
    list: async (projectId = null) => {
      const url = projectId 
        ? `${API_BASE_URL}/todos/?project_id=${projectId}`
        : `${API_BASE_URL}/todos/`;
      const response = await fetch(url, {
        method: 'GET',
        headers: getHeaders(),
      });
      return handleResponse(response);
    },
    create: async (todoData) => {
      const response = await fetch(`${API_BASE_URL}/todos/`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(todoData),
      });
      return handleResponse(response);
    },
    update: async (id, todoData) => {
      const response = await fetch(`${API_BASE_URL}/todos/${id}`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify(todoData),
      });
      return handleResponse(response);
    },
    delete: async (id) => {
      const response = await fetch(`${API_BASE_URL}/todos/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
      });
      return handleResponse(response);
    }
  },

  timeline: {
    list: async (projectId = null) => {
      const url = projectId 
        ? `${API_BASE_URL}/timeline/?project_id=${projectId}`
        : `${API_BASE_URL}/timeline/`;
      const response = await fetch(url, {
        method: 'GET',
        headers: getHeaders(),
      });
      return handleResponse(response);
    },
    create: async (eventData) => {
      const response = await fetch(`${API_BASE_URL}/timeline/`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(eventData),
      });
      return handleResponse(response);
    },
    update: async (id, eventData) => {
      const response = await fetch(`${API_BASE_URL}/timeline/${id}`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify(eventData),
      });
      return handleResponse(response);
    }
  },
  
  payments: {
    list: async () => {
      const response = await fetch(`${API_BASE_URL}/payments/`, {
        method: 'GET',
        headers: getHeaders(),
      });
      return handleResponse(response);
    },
    create: async (paymentData) => {
      const response = await fetch(`${API_BASE_URL}/payments/`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(paymentData),
      });
      return handleResponse(response);
    },
    delete: async (id) => {
      const response = await fetch(`${API_BASE_URL}/payments/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
      });
      return handleResponse(response);
    },
    sync: async () => {
      return { message: "Google Sheets integration is disabled." };
    }
  },

  contracts: {
    list: async () => {
      const response = await fetch(`${API_BASE_URL}/contracts/`, {
        method: 'GET',
        headers: getHeaders(),
      });
      return handleResponse(response);
    },
    create: async (formData) => {
      const headers = getHeaders();
      delete headers['Content-Type'];
      const response = await fetch(`${API_BASE_URL}/contracts/`, {
        method: 'POST',
        headers: headers,
        body: formData,
      });
      return handleResponse(response);
    },
    delete: async (id) => {
      const response = await fetch(`${API_BASE_URL}/contracts/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
      });
      return handleResponse(response);
    }
  },

  pendingThings: {
    list: async () => {
      const response = await fetch(`${API_BASE_URL}/pending-things/`, {
        method: 'GET',
        headers: getHeaders(),
      });
      return handleResponse(response);
    },
    create: async (formData) => {
      const headers = getHeaders();
      delete headers['Content-Type'];
      const response = await fetch(`${API_BASE_URL}/pending-things/`, {
        method: 'POST',
        headers: headers,
        body: formData,
      });
      return handleResponse(response);
    },
    update: async (id, data) => {
      const response = await fetch(`${API_BASE_URL}/pending-things/${id}`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify(data),
      });
      return handleResponse(response);
    },
    delete: async (id) => {
      const response = await fetch(`${API_BASE_URL}/pending-things/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
      });
      return handleResponse(response);
    }
  },

  ai: {
    process: async (rawInput, googleToken = null, sessionId = null) => {
      const response = await fetch(`${API_BASE_URL}/ai/process`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ 
          raw_input: rawInput, 
          google_token: googleToken || localStorage.getItem('google_token'),
          timezone_offset: new Date().getTimezoneOffset(),
          local_time: new Date().toISOString(),
          session_id: sessionId
        }),
      });
      return handleResponse(response);
    },
    transcribe: async (audioBlob) => {
      const headers = getHeaders();
      delete headers['Content-Type'];
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');
      
      const response = await fetch(`${API_BASE_URL}/ai/transcribe`, {
        method: 'POST',
        headers: headers,
        body: formData,
      });
      return handleResponse(response);
    },
    feedback: async (rating, feedbackText = null) => {
      const response = await fetch(`${API_BASE_URL}/ai/feedback`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ rating, feedback_text: feedbackText }),
      });
      return handleResponse(response);
    },
    listSessions: async () => {
      const response = await fetch(`${API_BASE_URL}/ai/sessions`, {
        method: 'GET',
        headers: getHeaders(),
      });
      return handleResponse(response);
    },
    renameSession: async (sessionId, title) => {
      const response = await fetch(`${API_BASE_URL}/ai/sessions/${sessionId}/rename?title=${encodeURIComponent(title)}`, {
        method: 'PUT',
        headers: getHeaders(),
      });
      return handleResponse(response);
    },
    deleteSession: async (sessionId) => {
      const response = await fetch(`${API_BASE_URL}/ai/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: getHeaders(),
      });
      return handleResponse(response);
    }
  },

  sync: {
    googleAuth: async () => {
      const response = await fetch(`${API_BASE_URL}/sync/google/auth`, {
        method: 'GET',
        headers: getHeaders(),
      });
      return handleResponse(response);
    },
    sheets: async (accessToken, projectId) => {
      const response = await fetch(`${API_BASE_URL}/sync/sheets`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ access_token: accessToken, project_id: projectId }),
      });
      return handleResponse(response);
    },
    calendar: async (accessToken, projectId) => {
      const response = await fetch(`${API_BASE_URL}/sync/calendar`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ access_token: accessToken, project_id: projectId }),
      });
      return handleResponse(response);
    },
    github: async (token, repo, projectId) => {
      const response = await fetch(`${API_BASE_URL}/sync/github`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ token, repo, project_id: projectId }),
      });
      return handleResponse(response);
    },
    getSheetsLinks: async () => {
      const response = await fetch(`${API_BASE_URL}/sync/sheets/links`, {
        method: 'GET',
        headers: getHeaders(),
      });
      return handleResponse(response);
    }
  },

  reminders: {
    list: async () => {
      const response = await fetch(`${API_BASE_URL}/reminders/`, {
        method: 'GET',
        headers: getHeaders(),
      });
      return handleResponse(response);
    },
    create: async (data) => {
      const response = await fetch(`${API_BASE_URL}/reminders/`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(data),
      });
      return handleResponse(response);
    },
    update: async (id, data) => {
      const response = await fetch(`${API_BASE_URL}/reminders/${id}`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify(data),
      });
      return handleResponse(response);
    },
    delete: async (id) => {
      const response = await fetch(`${API_BASE_URL}/reminders/${id}`, {
        method: 'DELETE',
        headers: getHeaders(),
      });
      return handleResponse(response);
    },
    clear: async () => {
      const response = await fetch(`${API_BASE_URL}/reminders/`, {
        method: 'DELETE',
        headers: getHeaders(),
      });
      return handleResponse(response);
    }
  }
};
