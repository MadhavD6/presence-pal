
import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowLeft, Loader2, Lock, User } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { authApi } from "@/services/api";
import { useAuth } from "@/context/AuthContext";

interface EmployeeLoginProps {
    onBack: () => void;
    onLoginSuccess: () => void;
}

const EmployeeLogin: React.FC<EmployeeLoginProps> = ({ onBack, onLoginSuccess }) => {
    const [identifier, setIdentifier] = useState(''); // Email or Employee ID
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { toast } = useToast();
    const { login } = useAuth();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!identifier || !password) {
            toast({
                title: "Error",
                description: "Please enter both credentials",
                variant: "destructive",
            });
            return;
        }

        setIsLoading(true);
        try {
            const data = await authApi.login(identifier, password);
            login(data.access_token);
            toast({
                title: "Success",
                description: "Logged in successfully",
            });
            // Delay to ensure localStorage sync completes
            setTimeout(() => {
                onLoginSuccess();
            }, 250);
        } catch (error: any) {
            toast({
                title: "Login Failed",
                description: error.message || "Invalid credentials",
                variant: "destructive",
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-background z-50 flex flex-col items-center justify-center p-4 animate-in fade-in duration-300">
            {/* Header */}
            <div className="absolute top-0 left-0 right-0 p-4 flex items-center">
                <Button variant="ghost" size="icon" onClick={onBack}>
                    <ArrowLeft className="w-6 h-6" />
                </Button>
            </div>

            <div className="w-full max-w-sm space-y-6">
                <div className="text-center space-y-2">
                    <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Lock className="w-8 h-8 text-primary" />
                    </div>
                    <h1 className="text-3xl font-bold tracking-tight">Employee Login</h1>
                    <p className="text-muted-foreground">Enter your credentials to access your dashboard</p>
                </div>

                <form onSubmit={handleLogin} className="space-y-4">
                    <div className="space-y-2">
                        <div className="relative">
                            <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Email or Employee ID"
                                className="pl-9"
                                value={identifier}
                                onChange={(e) => setIdentifier(e.target.value)}
                                disabled={isLoading}
                            />
                        </div>
                    </div>
                    <div className="space-y-2">
                        <div className="relative">
                            <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                            <Input
                                type="password"
                                placeholder="Password"
                                className="pl-9"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    <Button type="submit" className="w-full" disabled={isLoading}>
                        {isLoading ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Logging in...
                            </>
                        ) : (
                            "Login"
                        )}
                    </Button>
                </form>

                <div className="text-center text-sm text-muted-foreground">
                    <p>Protected by Kiosk Security</p>
                </div>
            </div>
        </div>
    );
};

export default EmployeeLogin;
