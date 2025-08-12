import { createBrowserRouter } from 'react-router-dom';
import Home from './pages/Home';
import PhaseOne from './pages/PhaseOne';

export const router = createBrowserRouter([
  {
    path: '/dashboard-preview',
    element: <Home />,
  },
  {
    path: '/dashboard-preview/phase-1',
    element: <PhaseOne />,
  },
  {
    path: '/',
    element: <Home />,
  },
  {
    path: '/phase-1',
    element: <PhaseOne />,
  },
]);