// ============================================================
// 🧪 TEST CREDENTIALS BANNER
// REMOVE THIS ENTIRE FILE DURING INTEGRATION
// Location: src/components/TestBanner.tsx
// ============================================================

import { TEST_CREDENTIALS } from "@/lib/mock-api";
import { FlaskConical } from "lucide-react";

const TestBanner = () => {
  return (
    <div className="w-full rounded-xl border border-primary/30 bg-accent p-4 mb-6">
      <div className="flex items-center gap-2 mb-3">
        <FlaskConical className="w-4 h-4 text-primary" />
        <span className="text-xs font-semibold uppercase tracking-wider text-primary">
          Test Mode
        </span>
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
        <span className="text-muted-foreground">Email:</span>
        <span className="font-mono text-foreground">{TEST_CREDENTIALS.email}</span>
        <span className="text-muted-foreground">Password:</span>
        <span className="font-mono text-foreground">{TEST_CREDENTIALS.password}</span>
        <span className="text-muted-foreground">MFA Code:</span>
        <span className="font-mono text-foreground">{TEST_CREDENTIALS.mfaCode}</span>
      </div>
    </div>
  );
};

export default TestBanner;
