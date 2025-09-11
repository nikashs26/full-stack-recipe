import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, Users, UserPlus, RefreshCw } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
  last_login?: string;
  is_active: boolean;
}

interface UserManagementProps {
  onClose: () => void;
}

export const UserManagement: React.FC<UserManagementProps> = ({ onClose }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [totalUsers, setTotalUsers] = useState(0);

  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://dietary-delight.onrender.com';

  const fetchUsers = async () => {
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(`${backendUrl}/api/auth/admin/users`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (data.success) {
        setUsers(data.users);
        setTotalUsers(data.total_users);
      } else {
        setError(data.error || 'Failed to fetch users');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (isLoading) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            User Management
          </CardTitle>
          <CardDescription>
            Manage user accounts and view system statistics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin" />
            <span className="ml-2">Loading users...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              User Management
            </CardTitle>
            <CardDescription>
              Manage user accounts and view system statistics
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={fetchUsers}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="outline" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-blue-600" />
              <span className="text-sm font-medium text-blue-600">Total Users</span>
            </div>
            <p className="text-2xl font-bold text-blue-900">{totalUsers}</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center gap-2">
              <UserPlus className="h-5 w-5 text-green-600" />
              <span className="text-sm font-medium text-green-600">Active Users</span>
            </div>
            <p className="text-2xl font-bold text-green-900">
              {users.filter(user => user.is_active).length}
            </p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="flex items-center gap-2">
              <RefreshCw className="h-5 w-5 text-purple-600" />
              <span className="text-sm font-medium text-purple-600">Recent Logins</span>
            </div>
            <p className="text-2xl font-bold text-purple-900">
              {users.filter(user => user.last_login).length}
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-lg font-semibold">User List</h3>
          {users.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No users found
            </div>
          ) : (
            <div className="space-y-2">
              {users.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium">{user.username}</span>
                      <Badge variant={user.is_active ? 'default' : 'secondary'}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{user.email}</p>
                    <div className="flex gap-4 text-xs text-muted-foreground mt-1">
                      <span>Joined: {formatDate(user.created_at)}</span>
                      {user.last_login && (
                        <span>Last login: {formatDate(user.last_login)}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
