import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { AuthProvider } from './lib/auth';
import { I18nProvider } from './lib/i18n';
import '@fontsource/noto-sans-ethiopic/ethiopic-400.css';
import '@fontsource/noto-sans-ethiopic/ethiopic-500.css';
import '@fontsource/noto-sans-ethiopic/ethiopic-700.css';
import '@fontsource/noto-serif-ethiopic/ethiopic-400.css';
import '@fontsource/noto-serif-ethiopic/ethiopic-500.css';
import '@fontsource/noto-serif-ethiopic/ethiopic-700.css';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <I18nProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </I18nProvider>
    </BrowserRouter>
  </React.StrictMode>
);
