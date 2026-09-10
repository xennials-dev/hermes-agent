// Global ambient module declarations for third-party and workspace UI packages

declare module 'lucide-react' {
  import * as React from 'react';
  export const Eye: React.ComponentType<any>;
  export const EyeOff: React.ComponentType<any>;
  export const ExternalLink: React.ComponentType<any>;
  export const KeyRound: React.ComponentType<any>;
  export const MessageSquare: React.ComponentType<any>;
  export const Pencil: React.ComponentType<any>;
  export const Plus: React.ComponentType<any>;
  export const Save: React.ComponentType<any>;
  export const Settings: React.ComponentType<any>;
  export const Trash2: React.ComponentType<any>;
  export const X: React.ComponentType<any>;
  export const Zap: React.ComponentType<any>;
  export const ChevronDown: React.ComponentType<any>;
  export const ChevronRight: React.ComponentType<any>;
  export const Copy: React.ComponentType<any>;
  export const PanelRight: React.ComponentType<any>;
  export const RotateCcw: React.ComponentType<any>;
  export const Check: React.ComponentType<any>;
  export const Search: React.ComponentType<any>;
  export const RefreshCw: React.ComponentType<any>;
  export const FileText: React.ComponentType<any>;
  export const Terminal: React.ComponentType<any>;
  export const Cpu: React.ComponentType<any>;
  export const Database: React.ComponentType<any>;
  export const Sparkles: React.ComponentType<any>;
  export const Download: React.ComponentType<any>;
  export const Upload: React.ComponentType<any>;
  export const Play: React.ComponentType<any>;
  export const Pause: React.ComponentType<any>;
  export const Clock: React.ComponentType<any>;
  export const User: React.ComponentType<any>;
  export const Users: React.ComponentType<any>;
}

declare module '@nous-research/ui/*' {
  const content: any;
  export default content;
  export * from '@nous-research/ui';
}

declare module '@nous-research/ui' {
  export const Toast: any;
  export const Button: any;
  export const ListItem: any;
  export const Spinner: any;
  export const Card: any;
  export const CardContent: any;
  export const CardDescription: any;
  export const CardHeader: any;
  export const CardTitle: any;
  export const Badge: any;
  export const Input: any;
  export const Label: any;
  export const useConfirmDelete: any;
  export const useToast: any;
}
