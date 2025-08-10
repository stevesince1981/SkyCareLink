# MediFly Hospital App

## Overview
MediFly is a Flask-based web application simulating a hospital interface for managing air medical transport services. It streamlines patient transport coordination from intake to flight completion, featuring a multi-step form, enhanced provider comparison, booking confirmation, real-time flight tracking simulation, intelligent chatbot assistance with severity-based recommendations, and HIPAA-compliant administrative oversight. The project aims to provide an efficient, transparent, and scalable solution for medical transport logistics, incorporating a fairness system for provider quote distribution, a hybrid provider search, and a comprehensive commission accounting system. MediFly generates revenue through non-refundable deposits and a commission structure per booking.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
- **Branding**: MediFly branding with helicopter + aircraft icons.
- **Theme**: Defaulting to a calming light blue theme.
- **Layout**: Jinja2 templates with a base template system for consistent layout, styled with Bootstrap 5.
- **Visuals**: Enhanced provider comparison with larger pricing displays and capability badges, improved hover animations, smooth progress bar transitions, priority partner pulse animations, and responsive design for mobile compatibility.
- **Accessibility**: ARIA labels and semantic HTML for screen reader compatibility.

### Technical Implementations
- **Web Framework**: Flask with session-based state management.
- **Authentication**: Simplified session-based, role-based authentication (Family, Hospital, Provider, MVP, Admin) with role-specific dashboards. Demo login credentials provided.
- **Data Handling**: Session-based temporary storage; intentionally database-free for demonstration. In-memory dictionaries for mock provider data and tracking stages.
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