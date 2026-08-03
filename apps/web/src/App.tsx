import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { Layout } from '@/components/Layout';
import { Dashboard } from '@/pages/Dashboard';
import { NewRequest } from '@/pages/NewRequest';
import { FeatureDetail } from '@/pages/FeatureDetail';
import { Backlog } from '@/pages/Backlog';
import { Approvals } from '@/pages/Approvals';
import { AgentRuns } from '@/pages/AgentRuns';
import { PullRequests } from '@/pages/PullRequests';
import { Settings } from '@/pages/Settings';
import { Projects } from '@/pages/Projects';

const router = createBrowserRouter([
    {
        path: '/',
        element: <Layout />,
        children: [
            { index: true, element: <Dashboard /> },
            { path: 'new', element: <NewRequest /> },
            { path: 'projects', element: <Projects /> },
            { path: 'features/:id', element: <FeatureDetail /> },
            { path: 'backlog', element: <Backlog /> },
            { path: 'approvals', element: <Approvals /> },
            { path: 'agents', element: <AgentRuns /> },
            { path: 'delivery', element: <PullRequests /> },
            { path: 'settings', element: <Settings /> },
        ],
    },
]);

export function App() {
    return <RouterProvider router={router} />;
}
