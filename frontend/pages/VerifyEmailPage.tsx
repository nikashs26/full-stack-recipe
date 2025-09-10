import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '@/hooks/use-toast';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, XCircle, Loader2, Mail } from 'lucide-react';

const VerifyEmailPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { verifyEmail, resendVerification } = useAuth();
  const { toast } = useToast();
  
  const [verificationStatus, setVerificationStatus] = useState<'loading' | 'success' | 'error' | 'expired'>('loading');
  const [errorMessage, setErrorMessage] = useState('');
  const [isResending, setIsResending] = useState(false);

  const token = searchParams.get('token');

  useEffect(() => {
    const verifyToken = async () => {
      if (!token) {
        setVerificationStatus('error');
        setErrorMessage('No verification token provided');
        return;
      }

      try {
        const result = await verifyEmail(token);
        
        if (result.success) {
          setVerificationStatus('success');
          // Redirect to sign in page after 3 seconds
          setTimeout(() => {
            navigate('/signin');
          }, 3000);
        } else {
          setVerificationStatus('error');
          setErrorMessage(result.error?.message || 'Verification failed');
          
          // Check if error indicates expired token
          if (result.error?.message?.toLowerCase().includes('expired')) {
            setVerificationStatus('expired');
          }
        }
      } catch (error) {
        setVerificationStatus('error');
        setErrorMessage('Network error occurred');
      }
    };

    verifyToken();
  }, [token, verifyEmail, navigate]);

  const handleResendVerification = async () => {
    const email = prompt('Please enter your email address to resend verification:');
    
    if (!email) return;

    setIsResending(true);
    try {
      const result = await resendVerification(email);
      
      if (result.success) {
        toast({
          title: "Verification email sent",
          description: "Please check your email for a new verification link.",
        });
      } else {
        toast({
          title: "Failed to resend",
          description: result.error?.message || "Please try again later.",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Network error occurred. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsResending(false);
    }
  };

  const handleGoToSignIn = () => {
    navigate('/signin');
  };

  const handleGoHome = () => {
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-amber-50">
      <Header />
      
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-md mx-auto">
          <Card>
            <CardHeader className="text-center">
              <div className="flex justify-center mb-4">
                {verificationStatus === 'loading' && (
                  <Loader2 className="h-16 w-16 text-blue-500 animate-spin" />
                )}
                {verificationStatus === 'success' && (
                  <CheckCircle className="h-16 w-16 text-green-500" />
                )}
                {(verificationStatus === 'error' || verificationStatus === 'expired') && (
                  <XCircle className="h-16 w-16 text-red-500" />
                )}
              </div>
              
              <CardTitle className="text-2xl">
                {verificationStatus === 'loading' && 'Verifying Your Email...'}
                {verificationStatus === 'success' && 'Email Verified Successfully!'}
                {verificationStatus === 'error' && 'Verification Failed'}
                {verificationStatus === 'expired' && 'Verification Link Expired'}
              </CardTitle>
              
              <CardDescription>
                {verificationStatus === 'loading' && 'Please wait while we verify your email address.'}
                {verificationStatus === 'success' && 'Your account has been verified. You can now sign in and start using all features.'}
                {verificationStatus === 'error' && 'There was a problem verifying your email address.'}
                {verificationStatus === 'expired' && 'This verification link has expired. Please request a new one.'}
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              {verificationStatus === 'success' && (
                <div className="space-y-4">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-green-800">
                      <CheckCircle className="h-5 w-5" />
                      <span className="font-medium">Account activated!</span>
                    </div>
                    <p className="text-green-700 text-sm mt-1">
                      You now have access to AI meal planning, shopping lists, and preferences.
                    </p>
                  </div>
                  
                  <Button onClick={handleGoToSignIn} className="w-full">
                    Sign In Now
                  </Button>
                  
                  <p className="text-center text-sm text-gray-500">
                    Redirecting to sign in page in 3 seconds...
                  </p>
                </div>
              )}

              {(verificationStatus === 'error' || verificationStatus === 'expired') && (
                <div className="space-y-4">
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-red-800">
                      <XCircle className="h-5 w-5" />
                      <span className="font-medium">Verification Failed</span>
                    </div>
                    <p className="text-red-700 text-sm mt-1">{errorMessage}</p>
                  </div>

                  {verificationStatus === 'expired' && (
                    <Button 
                      onClick={handleResendVerification} 
                      disabled={isResending}
                      className="w-full"
                      variant="outline"
                    >
                      {isResending ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Sending...
                        </>
                      ) : (
                        <>
                          <Mail className="h-4 w-4 mr-2" />
                          Resend Verification Email
                        </>
                      )}
                    </Button>
                  )}

                  <div className="flex gap-2">
                    <Button onClick={handleGoToSignIn} variant="outline" className="flex-1">
                      Try Sign In
                    </Button>
                    <Button onClick={handleGoHome} variant="ghost" className="flex-1">
                      Go Home
                    </Button>
                  </div>
                </div>
              )}

              {verificationStatus === 'loading' && (
                <div className="text-center">
                  <p className="text-sm text-gray-500">
                    This may take a few moments...
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default VerifyEmailPage; 