---
version: alpha
name: Codecademy
description: >-
  A tech-forward learning platform that transforms skill development into an accessible, energetic experience through
  bold color contrasts and modern typography.
logo:
  src: https://www.codecademy.com/apple-touch-icon.png
colors:
  surface: '#ffffff'
  surface-dim: '#f5f5f5'
  surface-bright: '#ffffff'
  surface-container-lowest: '#eeeeee'
  surface-container-low: '#f5f5f5'
  surface-container: '#ffffff'
  surface-container-high: '#f5f5f5'
  surface-container-highest: '#eeeeee'
  on-surface: '#10162f'
  on-surface-variant: '#616161'
  inverse-surface: '#10162f'
  inverse-on-surface: '#ffffff'
  outline: '#9e9e9e'
  outline-variant: '#e0e0e0'
  surface-tint: '#3a10e5'
  primary: '#3a10e5'
  on-primary: '#ffffff'
  primary-container: '#5533ff'
  on-primary-container: '#ffffff'
  inverse-primary: '#ffd300'
  secondary: '#10162f'
  on-secondary: '#ffffff'
  secondary-container: '#1d2340'
  on-secondary-container: '#ffffff'
  tertiary: '#ffd300'
  on-tertiary: '#10162f'
  tertiary-container: '#fffae5'
  on-tertiary-container: '#211b00'
  error: '#e91c11'
  on-error: '#ffffff'
  error-container: '#fbf1f0'
  on-error-container: '#280503'
  primary-fixed: '#5533ff'
  primary-fixed-dim: '#3a10e5'
  on-primary-fixed: '#ffffff'
  on-primary-fixed-variant: '#ffffff'
  secondary-fixed: '#1d2340'
  secondary-fixed-dim: '#10162f'
  on-secondary-fixed: '#ffffff'
  on-secondary-fixed-variant: '#ffffff'
  tertiary-fixed: '#ffd300'
  tertiary-fixed-dim: '#cca900'
  on-tertiary-fixed: '#10162f'
  on-tertiary-fixed-variant: '#211b00'
  background: '#ffffff'
  on-background: '#10162f'
  surface-variant: '#e0e0e0'
typography:
  display:
    fontFamily: Apercu
    fontSize: 76px
    fontWeight: '400'
    lineHeight: 84px
    letterSpacing: '-0.02em'
  headline-lg:
    fontFamily: Apercu
    fontSize: 44px
    fontWeight: '700'
    lineHeight: 52px
    letterSpacing: '-0.015em'
  headline-md:
    fontFamily: Apercu
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: '-0.01em'
  title-lg:
    fontFamily: Apercu
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  body-lg:
    fontFamily: Apercu
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Apercu
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Apercu
    fontSize: 14px
    fontWeight: '700'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Apercu
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 40px
  xl: 64px
  gutter: 24px
  container-max: 1440px
elevation:
  sm: 0 1px 2px rgba(16, 22, 47, 0.06)
  md: 0 4px 12px rgba(16, 22, 47, 0.08)
  lg: 0 10px 100px rgba(255, 211, 1, 0.31)
layout:
  containerMaxWidth: 1440px
  gridColumns: 12
components:
  button-primary:
    backgroundColor: '{colors.tertiary}'
    textColor: '{colors.on-tertiary}'
    typography: '{typography.label-md}'
    rounded: '{rounded.DEFAULT}'
    padding: 4px 16px
    height: 40px
    fontWeight: '700'
  button-primary-hover:
    backgroundColor: '{colors.tertiary-fixed-dim}'
    textColor: '{colors.on-tertiary}'
    transition: background-color 150ms ease-in-out
  button-secondary:
    backgroundColor: '{colors.secondary}'
    textColor: '{colors.on-secondary}'
    typography: '{typography.label-md}'
    rounded: '{rounded.DEFAULT}'
    padding: 4px 16px
    height: 40px
    fontWeight: '700'
  button-secondary-hover:
    backgroundColor: '{colors.secondary-fixed-dim}'
    textColor: '{colors.on-secondary}'
    transition: background-color 150ms ease-in-out
  button-ghost:
    backgroundColor: transparent
    textColor: '{colors.primary}'
    typography: '{typography.label-md}'
    rounded: '{rounded.DEFAULT}'
    padding: 4px 16px
    height: 40px
    border: 1px solid {colors.primary}
  button-ghost-hover:
    backgroundColor: rgba(58, 16, 229, 0.08)
    textColor: '{colors.primary}'
    transition: background-color 150ms ease-in-out
  card:
    backgroundColor: '{colors.surface}'
    rounded: '{rounded.lg}'
    padding: '{spacing.md}'
    boxShadow: '{elevation.md}'
    border: 1px solid {colors.outline-variant}
  card-hover:
    backgroundColor: '{colors.surface-dim}'
    boxShadow: '{elevation.lg}'
    transition: background-color 150ms ease-in-out, box-shadow 150ms ease-in-out
  input-field:
    backgroundColor: '{colors.surface}'
    textColor: '{colors.on-surface}'
    typography: '{typography.body-md}'
    rounded: '{rounded.DEFAULT}'
    padding: '{spacing.sm}'
    border: 1px solid {colors.outline-variant}
    height: 40px
  input-field-focus:
    borderColor: '{colors.primary}'
    boxShadow: 0 0 0 3px rgba(58, 16, 229, 0.1)
    transition: border-color 150ms ease-in-out, box-shadow 150ms ease-in-out
  badge:
    backgroundColor: '{colors.tertiary-container}'
    textColor: '{colors.on-tertiary-container}'
    typography: '{typography.label-sm}'
    rounded: '{rounded.full}'
    padding: 4px 12px
    display: inline-block
  badge-error:
    backgroundColor: '{colors.error-container}'
    textColor: '{colors.on-error-container}'
  list-item:
    backgroundColor: transparent
    rounded: '{rounded.md}'
    padding: '{spacing.sm}'
    textColor: '{colors.on-surface}'
  list-item-hover:
    backgroundColor: '{colors.surface-container-high}'
    textColor: '{colors.primary}'
    transition: background-color 150ms ease-in-out, color 150ms ease-in-out
---

## Overview

Codecademy is a tech-forward learning platform that democratizes skill development through bold, energetic design. The brand embodies "Vibrant Pragmatism"—a design philosophy that balances high-contrast color (electric purple #3A10E5 paired with vivid yellow #FFD300) with clean, accessible typography to make complex technical concepts feel approachable and exciting. The interface celebrates learning as an active, dynamic process: every interaction is crisp, every CTA unmissable, every surface purposeful. The emotional response is one of clarity and momentum—users feel empowered to begin, not intimidated.

The voice is direct, encouraging, and never patronizing. Codecademy speaks in imperative, action-oriented language: "Develop your skills," "Grow in your career," "Unlock new opportunities." The vocabulary avoids jargon when possible, but embraces technical terms when precision matters. Example sentence in brand voice: "Master Python in 8 weeks—then ship real projects with your new team."

## Colors

The color system operates on a principle of **Contrast-Driven Hierarchy**. Primary (#3A10E5, a saturated electric purple) is reserved exclusively for interactive elements—links, focus states, and secondary CTAs—creating a consistent signal for clickability. The true hero color is Tertiary (#FFD300, a warm, energetic yellow) used on primary call-to-action buttons and promotional banners; this yellow commands attention through warmth and saturation, not through ubiquity. Secondary (#10162F, a deep navy) anchors the interface as the text color and secondary button background, providing contrast and legibility. The surface stack uses near-white (#FFFFFF) as the primary canvas with carefully calibrated grays (surface-dim: #F5F5F5, outline-variant: #E0E0E0) for subtle layering without visual noi

## Typography

The type system centers on **Apercu**, a geometric sans-serif with clean proportions and excellent screen legibility. Display (76px, 400 weight, -0.02em letter-spacing) anchors hero sections with confident, spacious letterforms; Headline-lg (44px, 700 weight) breaks major sections; Body-md (16px, 400 weight, 24px line-height) ensures comfortable reading at standard viewing distances. The weight hierarchy is deliberate: body text stays at 400 to maximize readability, while labels and buttons jump to 700 to signal interactivity. Small labels (12px, 600 weight, 0.05em letter-spacing) receive expanded tracking to maintain legibility at reduced size and to add visual texture. Apply text-shadow: 0 2px 4px rgba(16, 22, 47, 0.15) on white text overlaid on photographic backgrounds (e.g., hero secti

## Layout

The layout follows a **12-column fluid grid** with a max-width of 1440px, centered with auto margins. Horizontal padding scales responsively: 16px on mobile (< 480px), 32px on tablet (480–768px), 64px on desktop (768px+), and 96px on large screens (1200px+). This creates a breathing room that prevents content from feeling cramped while maintaining focus. The spacing scale (unit: 8px) is used consistently: md (24px) for section separation, lg (40px) for major content blocks, and xl (64px) for hero-to-content transitions. Container max-width of 1440px ensures that even on ultra-wide displays, text remains scannable (optimal line length ~65–75 characters). White-space is treated as a design material, not wasted space: generous margins around cards (24px padding), loose line-height (1.5 for bo

## Elevation & Depth

Depth is conveyed through **Subtle Layering with Warm Shadows**. The elevation system uses three levels: (1) Base surfaces (cards, inputs) sit at 0 elevation with a 1px border in outline-variant (#E0E0E0) to define edges without shadow; (2) Elevated surfaces (hovered cards, modals) receive a soft shadow (0 4px 12px rgba(16, 22, 47, 0.08)) that suggests gentle lift; (3) Prominent surfaces (promotional banners, floating CTAs) use a warm, golden shadow (0 10px 100px rgba(255, 211, 1, 0.31)) that echoes the brand's yellow accent and creates visual warmth. Shadows are never pure black—they always t

## Shapes

The shape language is **Geometric Precision with Approachable Softness**. Buttons and inputs use 4px border-radius (rounded.DEFAULT), a subtle curve that feels modern without appearing playful or childish. Cards and larger containers use 16px (rounded.lg) to create visual distinction and breathing room. The 4px radius on buttons pairs with the 16px on cards to create a clear hierarchy: smaller radius = interactive, larger radius = container. Full-width badges and pills use 9999px (rounded.full) for a classic, friendly appearance. This tiered approach—4px for interaction, 16px for containment,

## Components

### Action Elements
Buttons are the primary interaction mechanism. Primary CTAs use the tertiary color (yellow #FFD300) with navy text (#10162F), 40px height, 4px radius, and 4px 16px padding. The high contrast (WCAG AAA) ensures visibility even in bright environments. On hover, the background shifts to tertiary-fixed-dim (#CCA900) with a 150ms ease-in-out transition, providing immediate feedback without animation fatigue. Secondary buttons invert: navy background with white text, used for less critical actions ("Log In") or secondary navigation. Ghost buttons (transparent background, purple border, purple text) are used for tertiary actions; on hover, they gain a subtle purple tint (rgba(58, 16, 229, 0.08)) to signal interactivity without overwhelming the layout.

### Containers & Surface

## Do's and Don'ts

**Do**
- Do use yellow (#FFD300) exclusively on primary CTAs and promotional elements—its rarity makes it a powerful attention magnet.
- Do maintain 24px padding inside cards and 40px gaps between major sections to create visual breathing room and reduce cognitive load.
- Do apply 150ms ease-in-out transitions on all interactive state changes (hover, focus, active) to signal responsiveness without feeling sluggish.
- Do use the navy (#10162F) as your primary text color on light backgrounds and white on dark backgrounds—never use gray for body text, as it reduces readability for learners.
- Do reserve the purple (#3A10E5) for secondary interactive elements (links, focus rings) to create a consistent signal for clickability without competing with yellow CTAs.

**Don't**
- Don't use yellow on backgrounds or large surface areas—it will overwhelm the interface and reduce the impact of CTAs.
- Don't mix rounded corners: stick to 4px for buttons/inputs, 16px for cards, 9999px for badges. Inconsistent radii create visual confusion.
- Don't apply shadows with pure black (rgba(0, 0, 0, x))—always tint shadows toward navy or use the warm yellow shadow for elevated elements to maintain brand warmth.
- Don't reduce line-height below 1.5 for body text or below 1.2 for headlines—tight leading reduces scannability and increases cognitive load for learners.
- Don't use more than two font weights in a single section—stick to 400 for body and 700 for emphasis to maintain visual clarity and hierarchy.
