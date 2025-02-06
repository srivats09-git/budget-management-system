# src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import AOPManagement from './components/AOPManagement';
import BudgetManagement from './components/BudgetManagement';
import UserManagement from './components/UserManagement';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <Navbar />
        <div className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/aop" element={<AOPManagement />} />
            <Route path="/budgets" element={<BudgetManagement />} />
            <Route path="/users" element={<UserManagement />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;

# src/components/Dashboard.js
import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { getActiveBudgets, getActiveAOP } from '../services/api';

const Dashboard = () => {
  const [budgetStats, setBudgetStats] = useState({
    totalBudget: 0,
    allocatedBudget: 0,
    remainingBudget: 0
  });
  const [activeAOP, setActiveAOP] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      const aop = await getActiveAOP();
      const budgets = await getActiveBudgets(aop.id);
      // Calculate stats
      const total = budgets.reduce((sum, b) => sum + b.amount, 0);
      setBudgetStats({
        totalBudget: total,
        allocatedBudget: total * 0.75, // Example calculation
        remainingBudget: total * 0.25
      });
      setActiveAOP(aop);
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Budget Management Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-6">
          <h3 className="font-semibold mb-2">Total Budget</h3>
          <p className="text-2xl">${budgetStats.totalBudget.toLocaleString()}</p>
        </Card>
        <Card className="p-6">
          <h3 className="font-semibold mb-2">Allocated</h3>
          <p className="text-2xl">${budgetStats.allocatedBudget.toLocaleString()}</p>
        </Card>
        <Card className="p-6">
          <h3 className="font-semibold mb-2">Remaining</h3>
          <p className="text-2xl">${budgetStats.remainingBudget.toLocaleString()}</p>
        </Card>
      </div>
    </div>
  );
};

# src/components/AOPManagement.js
import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { getAllAOPs, updateAOPState, createAOP } from '../services/api';

const AOPManagement = () => {
  const [aops, setAOPs] = useState([]);
  const [newAOPName, setNewAOPName] = useState('');

  useEffect(() => {
    fetchAOPs();
  }, []);

  const fetchAOPs = async () => {
    const data = await getAllAOPs();
    setAOPs(data);
  };

  const handleStateChange = async (aopId, newState) => {
    await updateAOPState(aopId, newState);
    fetchAOPs();
  };

  const handleCreateAOP = async () => {
    await createAOP(newAOPName);
    setNewAOPName('');
    fetchAOPs();
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">AOP Management</h1>
      
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Create New AOP</h2>
        <div className="flex gap-4">
          <input
            type="text"
            value={newAOPName}
            onChange={(e) => setNewAOPName(e.target.value)}
            className="flex h-10 rounded-md border border-input bg-white px-3 py-2 text-sm"
            placeholder="AOP Name"
          />
          <Button onClick={handleCreateAOP}>Create AOP</Button>
        </div>
      </Card>

      <div className="grid gap-4">
        {aops.map(aop => (
          <Card key={aop.id} className="p-6">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-semibold">{aop.name}</h3>
                <p className="text-sm text-gray-500">Current State: {aop.state}</p>
              </div>
              <div className="flex gap-2">
                <Button 
                  variant="outline"
                  onClick={() => handleStateChange(aop.id, 'draft')}
                  disabled={aop.state === 'draft'}
                >
                  Set Draft
                </Button>
                <Button
                  onClick={() => handleStateChange(aop.id, 'active')}
                  disabled={aop.state === 'active'}
                >
                  Set Active
                </Button>
                <Button 
                  variant="destructive"
                  onClick={() => handleStateChange(aop.id, 'EOL')}
                  disabled={aop.state === 'EOL'}
                >
                  Set EOL
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

# src/services/api.js
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8080';

export const getActiveBudgets = async (aopId) => {
  const response = await fetch(`${API_BASE_URL}/budgets?aop=${aopId}`);
  return response.json();
};

export const getActiveAOP = async () => {
  const response = await fetch(`${API_BASE_URL}/aop/active`);
  return response.json();
};

export const getAllAOPs = async () => {
  const response = await fetch(`${API_BASE_URL}/aop`);
  return response.json();
};

export const updateAOPState = async (aopId, newState) => {
  const response = await fetch(`${API_BASE_URL}/aop/${aopId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ state: newState }),
  });
  return response.json();
};

export const createAOP = async (name) => {
  const response = await fetch(`${API_BASE_URL}/aop`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name }),
  });
  return response.json();
};

# package.json
{
  "name": "budget-management-ui",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@testing-library/jest-dom": "^5.16.5",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^13.5.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.4.3",
    "react-scripts": "5.0.1",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }
}
