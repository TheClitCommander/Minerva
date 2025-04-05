/**
 * Minerva UI Component Exports
 * This file exports the Minerva 3D UI components for use in the browser
 */

// Import components
import MinervaUI from './MinervaUI.jsx';
import MinervaOrb from './MinervaOrb.jsx';
import { ThinkTankWidget } from './Widgets.jsx';

// Make components available globally for browser access
window.MinervaUI = MinervaUI;
window.MinervaOrb = MinervaOrb;
window.ThinkTankWidget = ThinkTankWidget;

// Export for module use
export {
  MinervaUI,
  MinervaOrb,
  ThinkTankWidget
};

// Export default component
export default MinervaUI;
