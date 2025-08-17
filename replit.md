# SkyCareLink Hospital App

## Overview
SkyCareLink is a Flask-based web application simulating a hospital interface for managing air medical transport services. It streamlines patient transport coordination from intake to flight completion. Key capabilities include a multi-step form, enhanced provider comparison, booking confirmation, real-time flight tracking simulation, intelligent chatbot assistance with severity-based recommendations, and HIPAA-compliant administrative oversight. The project aims to provide an efficient, transparent, and scalable solution for medical transport logistics, incorporating a fairness system for provider quote distribution, a hybrid provider search, and a comprehensive commission accounting system. SkyCareLink generates revenue through non-refundable deposits and a commission structure per booking.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
- **Branding**: SkyCareLink branding with helicopter + aircraft icons and professional medical team hero imagery, using a calming light blue theme.
- **Layout**: Jinja2 templates with a base template system for consistent layout, styled with Bootstrap 5.
- **Visuals**: Enhanced provider comparison with larger pricing displays and capability badges, improved hover animations, smooth progress bar transitions, priority partner pulse animations, and responsive design for mobile compatibility.
- **Accessibility**: ARIA labels and semantic HTML for screen reader compatibility.
- **Compact Design**: Utilizes "Pancake Accordion" design for collapsed subsections, reduced vertical whitespace, and compact form elements (service/severity cards, step numbers, navigation buttons, input fields) for efficient space usage.
- **Mobile-First Core Actions**: All quote/booking functions optimized for one-handed use on 360-414px width devices.

### Technical Implementations
- **Web Framework**: Flask with session-based state management.
- **React Dashboard**: Separate React + Vite + TypeScript + Tailwind application (`medifly-dashboard-sandbox/`) for a dashboard preview, integrated seamlessly with Flask.
- **Authentication**: Comprehensive role-based authentication (Family, Hospital, Provider, Affiliate, Admin) with PowerUser/TeamUser sub-role hierarchy, role-specific dashboards, and team management capabilities. CSRF protection using Flask-WTF on all POST forms, secure cookie flags, and 1-hour token lifetime.
- **Data Handling**: Hybrid approach combining session-based temporary storage for demo flows with PostgreSQL database for persistent data (users, bookings, commissions, analytics). Immutable document upload system with BLOB storage, SHA-256 hashing, and no-deletion enforcement.
- **Search**: Hybrid provider search system incorporating internal cache, Google Places integration stub, and manual fallback. Comprehensive hospital/clinic database with real-time search.
- **Commission System**: JSON-based ledger for booking commission tracking (4%/5% tiers), affiliate recoup tracking, and weekly invoice generation.
- **Transport Types**: Critical (same-day, 20% upcharge) and Non-Critical.
- **Equipment & Pricing**: Dynamic equipment pricing (e.g., Ventilator, ECMO), custom equipment option, and same-day upcharge. Severity levels (Level 1-3) auto-map to required equipment. Family seating standardized at $1,200 per seat.
- **AI Integration**: AI chat integration for natural language transport planning and smart form filling. AI IVR system via Twilio Voice webhook with DTMF routing.
- **Security**: HIPAA-compliant data masking in admin panel, session data protection, JWT token security with HMAC-SHA256 signing, no PHI storage. Enterprise audit trail system with file-based JSON logging (IP tracking, user agent, old/new value comparison), and specialized logging for sensitive actions. HTTP DELETE prevention. Security headers (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection).
- **Logging**: Python logging module for debugging. Database indexes for optimized query performance.

### Feature Specifications
- **Booking Flow**: Multi-step guided form for patient transport requests, including service type, severity levels, flight dates, location fields, contact information, COVID status, and medical needs. Form validation implemented for client/server.
- **Provider Comparison**: Enhanced comparison page showing ETA, aircraft type, certifications, and capabilities, with name blurring until booking confirmation.
- **Flight Tracking**: Real-time simulation with improved animations.
- **Chatbot**: Intelligent chatbot with severity-based equipment recommendations, detailed provider comparisons, pricing information, and real-time suggestions.
- **Administration**: Admin dashboards with revenue analytics, invoice management, affiliate management, modifiable business goals, and a comprehensive user management system with role-based permissions.
- **Consumer Features**: Landing page toggle for transport types, dynamic equipment pricing, AI command processing, address validation (Google Places API stub), provider competition fairness, and VIP services.
- **Partnerships**: CareCredit partnership integration for financing options and external payment links.
- **Notifications**: Affiliate notification system with email/SMS integration.
- **Document Management**: Professional upload interface with drag-and-drop, progress tracking, file validation, and comprehensive document listing with metadata.
- **Anti-Abuse System**: Enhanced deposit modal with admin override functionality.
- **Google Analytics 4**: Integration with custom event tracking for key user actions.

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
- **Twilio**: For AI IVR system and voice webhooks.
- **CDN Services**: For Bootstrap, Font Awesome, and BotUI.