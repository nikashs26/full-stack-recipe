
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
import { UserPlus, Loader2, Mail, CheckCircle, Eye, EyeOff } from 'lucide-react';

const formSchema = z.object({
  fullName: z.string().min(1, { message: 'Full name is required' }).max(100, { message: 'Name is too long' }),
  email: z.string().email({ message: 'Invalid email address' }),
  password: z.string()
    .min(8, { message: 'Password must be at least 8 characters' })
    .regex(/[A-Z]/, { message: 'Password must contain at least one uppercase letter' })
    .regex(/[a-z]/, { message: 'Password must contain at least one lowercase letter' })
    .regex(/\d/, { message: 'Password must contain at least one number' }),
  confirmPassword: z.string()
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

const SignUpPage: React.FC = () => {
  const { signUp, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [registrationSuccess, setRegistrationSuccess] = useState(false);
  const [verificationUrl, setVerificationUrl] = useState<string | null>(null);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      fullName: '',
      email: '',
      password: '',
      confirmPassword: ''
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
    if (isLoading) return;
    
    try {
      setIsLoading(true);
      console.log("Attempting to sign up with:", values.email);
      
      const result = await signUp(values.email, values.password, values.fullName);
      
      if (result.success) {
        console.log("Sign up successful");
        setRegistrationSuccess(true);
        setVerificationUrl(result.verificationUrl || null);
        
        // Reset form
        form.reset();
      } else {
        console.error("Sign up failed:", result.error);
        const errorMessage = result.error?.message || "An unexpected error occurred";
        
        // Set specific field errors if applicable
        if (errorMessage.toLowerCase().includes('email')) {
          form.setError("email", { message: errorMessage });
        } else if (errorMessage.toLowerCase().includes('password')) {
          form.setError("password", { message: errorMessage });
        } else {
          toast({
            title: "Sign up failed",
            description: errorMessage,
            variant: "destructive"
          });
        }
      }
      
    } catch (error: any) {
      console.error("Unexpected sign up error:", error);
      toast({
        title: "Sign up failed",
        description: "An unexpected error occurred. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoToSignIn = () => {
    navigate('/signin');
  };

  if (registrationSuccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 to-amber-50">
        <Header />
        
        <div className="container mx-auto px-4 py-16">
          <div className="max-w-md mx-auto">
            <Card>
              <CardHeader className="text-center">
                <div className="flex justify-center mb-4">
                  <CheckCircle className="h-16 w-16 text-green-500" />
                </div>
                <CardTitle className="text-2xl text-green-600">
                  Registration Successful!
                </CardTitle>
                <CardDescription>
                  We've sent a verification email to your address.
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-green-800">
                    <Mail className="h-5 w-5" />
                    <span className="font-medium">Check your email</span>
                  </div>
                  <p className="text-green-700 text-sm mt-1">
                    Click the verification link in your email to activate your account and access all features.
                  </p>
                </div>

                {verificationUrl && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-blue-800">
                      <span className="font-medium">Development Mode</span>
                    </div>
                    <p className="text-blue-700 text-sm mt-1">
                      For testing: <a href={verificationUrl} className="underline" target="_blank" rel="noopener noreferrer">
                        Click here to verify
                      </a>
                    </p>
                  </div>
                )}

                <Button onClick={handleGoToSignIn} className="w-full">
                  Go to Sign In
                </Button>

                <div className="text-center">
                  <p className="text-sm text-gray-600">
                    Didn't receive the email? Check your spam folder or{' '}
                    <Link to="/signin" className="text-blue-600 hover:underline">
                      try signing in
                    </Link>
                    {' '}to resend.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-amber-50">
      <Header />
      
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-md mx-auto">
          <Card>
            <CardHeader className="text-center">
              <div className="flex justify-center mb-4">
                <UserPlus className="h-12 w-12 text-orange-500" />
              </div>
              <CardTitle className="text-2xl">Create Your Account</CardTitle>
              <CardDescription>
                Join us to get personalized meal plans and recipes
              </CardDescription>
            </CardHeader>

            <CardContent>
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                  <FormField
                    control={form.control}
                    name="fullName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Full Name</FormLabel>
                        <FormControl>
                          <Input 
                            placeholder="Enter your full name" 
                            {...field}
                            disabled={isLoading}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

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
                            disabled={isLoading}
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
                              placeholder="Create a password" 
                              {...field}
                              disabled={isLoading}
                            />
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                              onClick={() => setShowPassword(!showPassword)}
                              disabled={isLoading}
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
                        <div className="text-xs text-gray-500 mt-1">
                          Must be 8+ characters with uppercase, lowercase, and number
                        </div>
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="confirmPassword"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Confirm Password</FormLabel>
                        <FormControl>
                          <div className="relative">
                            <Input 
                              type={showConfirmPassword ? "text" : "password"}
                              placeholder="Confirm your password" 
                              {...field}
                              disabled={isLoading}
                            />
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                              disabled={isLoading}
                            >
                              {showConfirmPassword ? (
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

                  <Button type="submit" className="w-full" disabled={isLoading}>
                    {isLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Creating account...
                      </>
                    ) : (
                      <>
                        <UserPlus className="h-4 w-4 mr-2" />
                        Create Account
                      </>
                    )}
                  </Button>

                  <div className="text-center">
                    <p className="text-sm text-gray-600">
                      Already have an account?{' '}
                      <Link to="/signin" className="text-blue-600 hover:underline">
                        Sign in here
                      </Link>
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

export default SignUpPage;
