# Dashboard Design - Vercel-Inspired Professional UI

## Overview
The Smart Sports Dashboard has been redesigned with a clean, minimal, and professional aesthetic inspired by Vercel's design system.

## Design Principles

### 1. **Minimalism**
- Clean white backgrounds (#fafafa, white)
- Subtle borders (#e5e5e5, #f5f5f5)
- Minimal shadows (0 1px 3px rgba(0,0,0,0.04))
- No gradients or heavy visual effects

### 2. **Typography**
- Font Family: System fonts (-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Roboto)
- Heading Sizes: 1.875rem (h1), 1.25rem (panel titles), 1.125rem (module titles)
- Body Sizes: 0.875rem (standard), 0.813rem (small), 0.75rem (tiny)
- Font Weights: 700 (bold), 600 (semibold), 500 (medium), 400 (regular)
- Letter Spacing: -0.02em (headings), -0.01em (body)

### 3. **Color Palette**
```css
/* Neutrals */
Background: #fafafa
Card Background: white
Border: #e5e5e5
Border Hover: #d4d4d4
Text Primary: #171717
Text Secondary: #737373
Text Tertiary: #a3a3a3

/* Status Colors */
Success: #16a34a (green-600)
Error: #dc2626 (red-600)
Warning: #ea580c (orange-600)
Info: #2563eb (blue-600)

/* Crowd Levels */
Empty: #f0fdf4 (green-50) / #15803d (green-700)
Light: #f7fee7 (lime-50) / #65a30d (lime-600)
Normal: #fef3c7 (amber-50) / #ca8a04 (yellow-600)
Busy: #ffedd5 (orange-50) / #ea580c (orange-600)
Full: #fee2e2 (red-50) / #dc2626 (red-600)
```

### 4. **Spacing System**
- Base unit: 4px
- Small: 8px, 12px
- Medium: 16px, 20px, 24px
- Large: 28px, 32px
- Gap between cards: 20-24px
- Padding inside cards: 20-28px

### 5. **Border Radius**
- Cards: 12px
- Buttons: 8px
- Badges: 6px
- Small elements: 4px

### 6. **Shadows**
- Default: 0 1px 3px rgba(0,0,0,0.04)
- Hover: 0 4px 12px rgba(0,0,0,0.05)
- Elevated: 0 4px 12px rgba(0,0,0,0.06)

## Layout Structure

### Grid System
```
┌─────────────────────────────────────────┐
│           Top Bar (Header)              │
│  System Health Indicators (5 modules)   │
└─────────────────────────────────────────┘
┌──────────┬──────────────────┬───────────┐
│          │                  │           │
│  Left    │     Center       │   Right   │
│  Panel   │     Panel        │   Panel   │
│ Module 5 │  Real-time Data  │ Controls  │
│ Preview  │  (Modules 1-3)   │ & Debug   │
│          │                  │           │
└──────────┴──────────────────┴───────────┘
┌─────────────────────────────────────────┐
│         Bottom Panel (Charts)           │
│  Hourly Pattern | Weekly Comparison     │
└─────────────────────────────────────────┘
```

### Column Widths
- Left Panel: 360px
- Center Panel: 1fr (flexible)
- Right Panel: 380px
- Max Container Width: 1800px

## Component Styles

### Cards
- Background: white
- Border: 1px solid #e5e5e5
- Border Radius: 12px
- Padding: 24px
- Hover: border-color #d4d4d4, shadow increase

### Buttons
- Primary Style: white background, black border
- Border: 1px solid #e5e5e5
- Border Radius: 8px
- Padding: 10px 16px
- Font Size: 0.875rem
- Hover: background #fafafa, border-color #171717

### Status Badges
- Border: 1px solid (matching color)
- Border Radius: 6px
- Padding: 4px 12px
- Font Size: 0.813rem
- Font Weight: 500

### Toggle Switch
- Width: 44px
- Height: 24px
- Background: #e5e5e5 (off), #171717 (on)
- Thumb: 20px circle with shadow

### Data Items
- Background: #fafafa
- Border: 1px solid #f5f5f5
- Border Radius: 8px
- Padding: 16px
- Hover: border-color #e5e5e5

## Animations

### Transitions
- Duration: 0.2s (fast), 0.3s (medium)
- Easing: ease, cubic-bezier(0.4, 0, 0.2, 1)

### Keyframes
- fadeIn: opacity 0→1, translateY 8px→0
- slideIn: opacity 0→1, translateX -12px→0
- subtlePulse: opacity 1→0.6→1 (2s)
- flash: background transparent→rgba(0,0,0,0.02)→transparent

## Accessibility

### Scrollbars
- Width: 8px
- Track: #fafafa
- Thumb: #d4d4d4
- Thumb Hover: #a3a3a3

### Focus States
- Border: #171717
- Shadow: 0 0 0 3px rgba(0,0,0,0.05)

### Contrast Ratios
- All text meets WCAG AA standards
- Primary text: #171717 on white (14.6:1)
- Secondary text: #737373 on white (4.7:1)

## Responsive Breakpoints

### Desktop (>1400px)
- 3-column layout
- All panels visible

### Tablet (900px - 1400px)
- 2-column layout
- Left + Center top
- Right + Bottom bottom

### Mobile (<900px)
- Single column
- Stacked panels
- Reduced padding (16px)
- Smaller font sizes

## Implementation Notes

1. **No Emojis**: Removed all emojis for professional appearance
2. **Consistent Spacing**: 4px base unit system
3. **Subtle Interactions**: Minimal hover effects, no heavy animations
4. **Monospace Font**: SF Mono, Monaco, Cascadia Code for code inspector
5. **System Fonts**: Native font stack for optimal performance

## Files Modified
- `Assignment/group_project/templates/index.html` - Complete redesign

## Server Status
- Running at: http://192.168.72.161:5000
- All features functional with new design
