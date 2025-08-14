# SkyCareLink Hospital App

## Overview
SkyCareLink is a Flask-based web application simulating a hospital interface for managing air medical transport services. It streamlines patient transport coordination from intake to flight completion, featuring a multi-step form, enhanced provider comparison, booking confirmation, real-time flight tracking simulation, intelligent chatbot assistance with severity-based recommendations, and HIPAA-compliant administrative oversight. The project aims to provide an efficient, transparent, and scalable solution for medical transport logistics, incorporating a fairness system for provider quote distribution, a hybrid provider search, and a comprehensive commission accounting system. SkyCareLink generates revenue through non-refundable deposits and a commission structure per booking.

## User Preferences
Preferred communication style: Simple, everyday language.

## Recent Changes (Phase 13.C SkyCareLink Rebranding Complete - Aug 14, 2025)
- **MVP Membership Removal**: Completely eliminated all MVP membership references from intake forms, service selection, and throughout the application
- **Intake Form Enhancements**: Fixed 415 error for form submissions, updated severity levels to "Level 1-3" format, equal-sized boxes (180px height, centered)
- **Hospital Autofill System**: Implemented comprehensive hospital/clinic database with 30+ major medical centers, real-time search with debouncing for From/To locations
- **Family Seating Standardization**: Updated to industry standard $1,200 per seat (previously $500), aircraft-specific availability messaging maintained
- **Same-Day Pricing Logic**: Moved 20% upcharge notice to date/time selection where logically appropriate, removed from service type cards
- **Legal Compliance Implementation**: Created comprehensive Terms of Service and Privacy Policy modals with standard industry language, liability protection, refund policies, HIPAA compliance
- **AI Assistant Updates**: Fixed home page AI bot with current information - updated pricing, removed MVP references, correct severity levels, industry-standard family seating costs
- **Technical Improvements**: Enhanced JSON/form data handling, hospital search API endpoint, modal integration for legal documents
- **State Management**: Dual storage (session + localStorage), form restoration after login flow, enhanced auto-save on all input changes
- **Provider Masking Logic**: Identity remains hidden until affiliate payment confirmation, booking code generation with preview display
- **User Management System**: Comprehensive role-based permissions for Affiliate, Hospital, Individual, and Admin accounts with PowerUser/TeamUser hierarchy
- **Portal Enhancement**: Expandable analytics cards with +/- controls, date-based filtering (day/week/month/year/custom), search capabilities, and revenue tracking
- **Team Management**: Owner/member permission system with promotion/demotion capabilities between PowerUser and TeamUser roles
- **Anti-Abuse System**: Enhanced deposit modal with admin override functionality and fair-use policy enforcement
- **React Dashboard Preview**: Built complete separate React + Vite + TypeScript + Tailwind application for Phase 1 dashboard demonstration
- **Split-Screen Interface**: Dual-pane dashboard showing Full View (left) with advanced filtering and Simplified View (right) with streamlined interface
- **Role-Based Data**: Dynamic role toggle (Affiliate/Provider/Individual) with different datasets and incentive indicators for each role
- **Interactive Features**: Working Accept buttons with toast notifications, confirmation modals, print functionality, and comprehensive quote management
- **Responsive Design**: Clean, accessible interface with sticky headers, expandable filters, and print-optimized styling
- **Flask Integration Complete**: Fixed routing issues, asset serving, and React Router configuration for seamless integration with Flask application
- **Critical Fixes Applied**: Asset path correction (/dashboard-preview/assets/), React Router Flask compatibility, comprehensive error handling
- **Complete Rebuild Documentation**: Created REACT_DASHBOARD_REBUILD_GUIDE.md with step-by-step instructions including all critical fixes
- **Complete Rebranding to SkyCareLink**: Systematically replaced all MediFly references with SkyCareLink throughout the entire system
- **Professional Hero Image Integration**: Added high-quality medical transport image showing professional medical team with aircraft
- **Enhanced Visual Design**: Dark overlay containers with proper text contrast, info-colored statistics, and improved readability
- **Configuration Updates**: Updated all SKYCARELINK_CONFIG variables and branding elements across templates and React components

## System Architecture

### UI/UX Decisions
- **Branding**: SkyCareLink branding with helicopter + aircraft icons and professional medical team hero imagery.
- **Theme**: Defaulting to a calming light blue theme.
- **Layout**: Jinja2 templates with a base template system for consistent layout, styled with Bootstrap 5.
- **Visuals**: Enhanced provider comparison with larger pricing displays and capability badges, improved hover animations, smooth progress bar transitions, priority partner pulse animations, and responsive design for mobile compatibility.
- **Accessibility**: ARIA labels and semantic HTML for screen reader compatibility.

### Technical Implementations
- **Web Framework**: Flask with session-based state management.
- **React Dashboard**: Separate React + Vite + TypeScript + Tailwind application (`medifly-dashboard-sandbox/`) for Phase 1 preview functionality.
- **Authentication**: Comprehensive role-based authentication (Family, Hospital, Provider, Affiliate, Admin) with PowerUser/TeamUser sub-role hierarchy, role-specific dashboards, and team management capabilities. Demo login credentials provided.
- **Data Handling**: Hybrid approach combining session-based temporary storage for demo flows with PostgreSQL database for persistent data (users, bookings, commissions, analytics).
- **Search**: Hybrid provider search system incorporating internal cache, Google Places integration stub, and manual fallback.
- **Commission System**: JSON-based ledger for booking commission tracking (4%/5% tiers), affiliate recoup tracking, and weekly invoice generation (CSV/HTML export).
- **Transport Types**: Critical (same-day, 20% upcharge), Non-Critical, and MVP Membership options.
- **Equipment & Pricing**: Dynamic equipment pricing (e.g., Ventilator, ECMO), custom equipment option, and same-day upcharge.
- **AI Integration**: AI chat integration for natural language transport planning and smart form filling.
- **Security**: HIPAA-compliant data masking in admin panel, session data protection, JWT token security with HMAC-SHA256 signing, and no PHI storage.
- **Logging**: Python logging module for debugging.

### Feature Specifications
- **Booking Flow**: Multi-step guided form for patient transport requests.
- **Provider Comparison**: Enhanced comparison page showing ETA, aircraft type, certifications, and capabilities, with name blurring until booking confirmation.
- **Flight Tracking**: Real-time simulation with improved animations.
- **Chatbot**: Intelligent chatbot with severity-based equipment recommendations, detailed provider comparisons, pricing information, and real-time suggestions.
- **Administration**: Admin dashboards with revenue analytics, invoice management, affiliate management, and modifiable business goals.
- **Consumer Features**: Landing page toggle for transport types, dynamic equipment pricing, AI command processing, address validation (Google Places API stub), provider competition fairness, and VIP services.
- **Partnerships**: CareCredit partnership integration for financing options and external payment links.

## External Dependencies

### Frontend Libraries
- **Bootstrap 5**: CSS framework via CDN.
- **Font Awesome 6**: Icon library via CDN.
- **BotUI**: Chatbot interface library.

### Backend Dependencies
- **Flask**: Core web framework.
- **Python Standard Library**: `datetime`, `os`, `logging` modules.

### Third-party Integrations
- **Google Places API (stubbed)**: For address autocomplete and validation.
- **CareCredit (conceptual)**: Integrated for financing options.
- **CDN Services**: For Bootstrap, Font Awesome, and BotUI.