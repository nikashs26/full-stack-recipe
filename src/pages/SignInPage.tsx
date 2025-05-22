
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '@/hooks/use-toast';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from '@/components/ui/form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { LogIn, Loader2, AlertTriangle, Mail } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";

const formSchema = z.object({
  email: z.string().email({ message: 'Invalid email address' }),
  password: z.string().min(6, { message: 'Password must be at least 6 characters' })
});

const SignInPage: React.FC = () => {
  const { signIn, isAuthenticated, isVerificationRequired, error, resetAuthError } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [showVerificationDialog, setShowVerificationDialog] = useState(false);
  const [verificationEmail, setVerificationEmail] = useState('');

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: '',
      password: ''
    }
  });

  // Reset auth errors when component unmounts
  useEffect(() => {
    return () => {
      resetAuthError();
    };
  }, [resetAuthError]);

  // Safety timeout to prevent UI from getting stuck
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    
    if (isLoading) {
      timer = setTimeout(() => {
        console.log('Sign in timeout reached, resetting loading state');
        setIsLoading(false);
        toast({
          title: "Sign in taking longer than expected",
          description: "Please try again or check your connection",
          variant: "destructive"
        });
      }, 10000); // 10 second timeout
    }
    
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [isLoading, toast]);

  // Redirect if authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  // Show verification dialog if needed
  useEffect(() => {
    if (isVerificationRequired) {
      setShowVerificationDialog(true);
      setVerificationEmail(form.getValues().email);
    }
  }, [isVerificationRequired, form]);

  // Reset verification dialog when form values change
  useEffect(() => {
    const subscription = form.watch(() => {
      setShowVerificationDialog(false);
    });
    return () => subscription.unsubscribe();
  }, [form]);

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    try {
      setIsLoading(true);
      console.log("Attempting to sign in with:", values.email);
      await signIn(values.email, values.password);
      toast({
        title: "Success!",
        description: "You're now signed in.",
      });
      // No need to navigate here - the useEffect will handle it
    } catch (error: any) {
      console.error("Sign in error:", error);
      // Toast notification will be shown for the error from AuthContext state
      setIsLoading(false); // Make sure loading state is reset on error
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="pt-24 md:pt-28">
        <div className="max-w-md mx-auto px-4 sm:px-6 py-12 bg-white shadow-sm rounded-lg mt-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold">Sign In</h1>
            <p className="text-gray-500 mt-2">Welcome back to Better Bulk</p>
          </div>

          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input placeholder="your@email.com" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input type="password" placeholder="••••••••" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button 
                type="submit" 
                className="w-full"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  <>
                    <LogIn className="mr-2 h-4 w-4" />
                    Sign In
                  </>
                )}
              </Button>
            </form>
          </Form>

          <div className="mt-6 text-center text-sm">
            <p>
              Don't have an account?{' '}
              <Link to="/signup" className="text-recipe-primary hover:underline">
                Sign Up
              </Link>
            </p>
          </div>

          {/* Email Verification Dialog */}
          <Dialog open={showVerificationDialog} onOpenChange={setShowVerificationDialog}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Email Verification Required</DialogTitle>
                <DialogDescription>
                  <div className="py-4">
                    <div className="flex items-center justify-center mb-4">
                      <Mail className="h-12 w-12 text-blue-500" />
                    </div>
                    <p className="mb-4">
                      We've sent a verification link to <strong>{verificationEmail}</strong>. Please check your inbox and verify your email before signing in.
                    </p>
                    <p className="text-sm text-gray-500">
                      If you don't see the email, please check your spam folder or try signing up again.
                    </p>
                  </div>
                </DialogDescription>
              </DialogHeader>
            </DialogContent>
          </Dialog>
        </div>
      </main>
    </div>
  );
};

export default SignInPage;
