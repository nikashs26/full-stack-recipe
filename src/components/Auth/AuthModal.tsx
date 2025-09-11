import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: any, token: string) => void;
  defaultMode?: 'login' | 'register';
}

export const AuthModal: React.FC<AuthModalProps> = ({ 
  isOpen, 
  onClose, 
  onSuccess, 
  defaultMode = 'login' 
}) => {
  const [mode, setMode] = useState<'login' | 'register'>(defaultMode);

  const handleSuccess = (user: any, token: string) => {
    onSuccess(user, token);
    onClose();
  };

  const switchToLogin = () => setMode('login');
  const switchToRegister = () => setMode('register');

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {mode === 'login' ? 'Sign In' : 'Create Account'}
          </DialogTitle>
        </DialogHeader>
        
        {mode === 'login' ? (
          <LoginForm 
            onSuccess={handleSuccess}
            onSwitchToRegister={switchToRegister}
          />
        ) : (
          <RegisterForm 
            onSuccess={handleSuccess}
            onSwitchToLogin={switchToLogin}
          />
        )}
      </DialogContent>
    </Dialog>
  );
};
