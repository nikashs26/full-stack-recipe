
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '@/hooks/use-toast';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from '@/components/ui/form';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { LogIn, Loader2, Mail, Eye, EyeOff } from 'lucide-react';

const formSchema = z.object({
  email: z.string().email({ message: 'Invalid email address' }),
  password: z.string().min(1, { message: 'Password is required' })
});

const SignInPage: React.FC = () => {
  const { signIn, isAuthenticated, isLoading: authLoading, resendVerification } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showResendVerification, setShowResendVerification] = useState(false);
  const [lastEmail, setLastEmail] = useState('');

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: '',
      password: ''
    }
  });

  // Redirect if authenticated
  useEffect(() => {
    if (isAuthenticated) {
      console.log("User is authenticated, redirecting to home");
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    if (isSubmitting) return;
    
    try {
      setIsSubmitting(true);
      setShowResendVerification(false);
      console.log("Attempting to sign in with:", values.email);
      
      const result = await signIn(values.email, values.password);
      
      if (result.success) {
        console.log("Sign in successful");
        // Navigation will happen automatically via useEffect when isAuthenticated changes
      } else {
        console.error("Sign in failed:", result.error);
        const errorMessage = result.error?.message || "Invalid email or password. Please check your credentials.";
        
        // Check if the error is related to email verification
        if (errorMessage.toLowerCase().includes('verify') || errorMessage.toLowerCase().includes('verification')) {
          setLastEmail(values.email);
          setShowResendVerification(true);
          toast({
            title: "Email verification required",
            description: "Please verify your email before signing in. Check your inbox or request a new verification email.",
            variant: "destructive"
          });
        } else {
          toast({
            title: "Sign in failed",
            description: errorMessage,
            variant: "destructive"
          });
        }
        
        form.setError("password", { message: "Invalid credentials" });
      }
      
    } catch (error: any) {
      console.error("Unexpected sign in error:", error);
      toast({
        title: "Sign in failed",
        description: "An unexpected error occurred. Please try again.",
        variant: "destructive"
      });
      form.setError("password", { message: "An error occurred during sign in" });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResendVerification = async () => {
    if (!lastEmail) {
      toast({
        title: "Email required",
        description: "Please enter your email first.",
        variant: "destructive"
      });
      return;
    }

    try {
      const result = await resendVerification(lastEmail);
      
      if (result.success) {
        setShowResendVerification(false);
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
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-amber-50">
      <Header />
      
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-md mx-auto">
          <Card>
            <CardHeader className="text-center">
              <div className="flex justify-center mb-4">
                <LogIn className="h-12 w-12 text-orange-500" />
              </div>
              <CardTitle className="text-2xl">Welcome Back</CardTitle>
              <CardDescription>
                Sign in to access your personalized meal plans
              </CardDescription>
            </CardHeader>

            <CardContent>
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                  <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Email</FormLabel>
                        <FormControl>
                          <Input 
                            type="email" 
                            placeholder="Enter your email" 
                            {...field}
                            disabled={isSubmitting || authLoading}
                            onChange={(e) => {
                              field.onChange(e);
                              setLastEmail(e.target.value);
                            }}
                          />
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
                          <div className="relative">
                            <Input 
                              type={showPassword ? "text" : "password"}
                              placeholder="Enter your password" 
                              {...field}
                              disabled={isSubmitting || authLoading}
                            />
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                              onClick={() => setShowPassword(!showPassword)}
                              disabled={isSubmitting || authLoading}
                            >
                              {showPassword ? (
                                <EyeOff className="h-4 w-4" />
                              ) : (
                                <Eye className="h-4 w-4" />
                              )}
                            </Button>
                          </div>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {showResendVerification && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <div className="flex items-center gap-2 text-yellow-800">
                        <Mail className="h-5 w-5" />
                        <span className="font-medium">Email verification required</span>
                      </div>
                      <p className="text-yellow-700 text-sm mt-1">
                        Please verify your email before signing in.
                      </p>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={handleResendVerification}
                        className="mt-2"
                      >
                        Resend Verification Email
                      </Button>
                    </div>
                  )}

                  <Button 
                    type="submit" 
                    className="w-full" 
                    disabled={isSubmitting || authLoading}
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Signing in...
                      </>
                    ) : (
                      <>
                        <LogIn className="h-4 w-4 mr-2" />
                        Sign In
                      </>
                    )}
                  </Button>

                  <div className="text-center space-y-2">
                    <p className="text-sm text-gray-600">
                      Don't have an account?{' '}
                      <Link to="/signup" className="text-blue-600 hover:underline">
                        Sign up here
                      </Link>
                    </p>
                    
                    <p className="text-xs text-gray-500">
                      By signing in, you agree to our terms of service and privacy policy
                    </p>
                  </div>
                </form>
              </Form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default SignInPage;
