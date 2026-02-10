import { Shield } from "lucide-react";

interface AuthLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
}

const AuthLayout = ({ children, title, subtitle }: AuthLayoutProps) => {
  return (
    <div className="flex min-h-screen">
      {/* Left decorative panel */}
      <div className="hidden lg:flex lg:w-1/2 auth-gradient items-center justify-center p-12 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="absolute rounded-full border border-primary/30"
              style={{
                width: `${200 + i * 120}px`,
                height: `${200 + i * 120}px`,
                top: "50%",
                left: "50%",
                transform: "translate(-50%, -50%)",
              }}
            />
          ))}
        </div>
        <div className="relative z-10 text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-primary/20 glow mb-8">
            <Shield className="w-10 h-10 text-primary" />
          </div>
          <h2 className="text-3xl font-bold text-white mb-4">Secure Authentication</h2>
          <p className="text-white/60 max-w-sm text-lg leading-relaxed">
            Multi-factor authentication for enhanced account security
          </p>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md">
          <div className="flex items-center gap-3 mb-2 lg:hidden">
            <Shield className="w-6 h-6 text-primary" />
            <span className="font-semibold text-foreground">SecureAuth</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground mb-1">{title}</h1>
          {subtitle && <p className="text-muted-foreground mb-8">{subtitle}</p>}
          <div className="mt-6">{children}</div>
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
