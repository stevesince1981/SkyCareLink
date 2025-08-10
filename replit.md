# MediFly Hospital MVP

## Overview

MediFly is a Flask-based web application that simulates a hospital interface for booking air medical transport services. The system provides a streamlined workflow for hospital staff to coordinate critical patient transports, from initial intake through flight tracking and completion. The application features a multi-step guided form, enhanced provider comparison with visual capability badges, booking confirmation, real-time flight tracking simulation with improved animations, intelligent chatbot assistance with severity-based recommendations, and administrative oversight capabilities with HIPAA-compliant data masking.

## Recent Enhancements (August 2025)

### Phase 4.A: Hybrid Provider Search Implementation (Latest - August 10, 2025)
- Implemented comprehensive hybrid provider search system with internal cache, Google Places integration, and manual fallback
- Created JSON-based data structure (`data/providers_index.json`) with 10 pre-populated providers across major medical centers and airports
- Added search metrics tracking (`data/search_metrics.json`) for Year 3 cost control KPIs
- Developed autocomplete functionality in intake forms with real-time provider search
- Implemented admin facilities management portal with approval queue for manual entries
- Added provider selection recording for popularity-based ranking system
- Enhanced intake form UI with "Can't find it? Add manually" links and search feedback
- All terminology standardized: "Affiliate" for air operators, "Hospital/Clinic" for requesters
- Application fully tested and running with no errors after hybrid search integration

### Simplified Authentication & Revenue Model (Latest - August 4, 2025)
- Removed professional theme switcher, defaulting to calming light blue theme
- Updated MediFly branding with helicopter + aircraft icons in navigation
- Implemented realistic revenue calculations: $1,000 non-refundable deposit + 5% commission per booking
- Created role-specific dashboards: Family (comfort-focused), Provider (earnings-focused), Admin (revenue analytics)
- Modifiable admin goals system with accurate financial projections
- Actual MediFly revenue: $49,375 (7 bookings × $1,000 deposits + $42,375 commission from $847,500 service value)

### Role-Based Authentication System
- Simplified session-based authentication without complex dependencies
- Role-based access control for Family, Hospital, Provider, MVP, and Admin users
- Role-specific dashboards with tailored interfaces and functionality
- Family users see comfort and support options, not revenue data
- Provider users see earnings and available requests, not company financials
- Admin users see comprehensive revenue analytics and modifiable business goals

### Admin Storyboard Demonstrations
- Interactive admin feature storyboard with live data visualization
- Business performance highlights showcasing $847,500 revenue achievement
- Comprehensive feature demonstrations including provider search, security scanning, and migration status
- Auto-demo mode with sequential feature walkthrough capabilities
- Timeline-based business intelligence presentation with growth metrics

### Enhanced Dashboard Suite
- Family Dashboard: Pastel-themed interface with family support features, comfort options, and privacy assurance
- Hospital Dashboard: Clinical-focused interface with bulk request management, HIPAA compliance tracking, and emergency protocols
- Provider Dashboard: Earnings tracking, bid management, flight planning tools, and performance metrics
- MVP Dashboard: Beta feature access, feedback collection, usage analytics, and exclusive early adopter perks

### Visual and UX Improvements
- Enhanced provider comparison page with larger pricing displays and capability badges
- Improved hover animations and transitions throughout the interface
- Enhanced progress bar styling with smooth transitions for flight tracking
- Responsive design improvements for better mobile compatibility

### Chatbot Intelligence
- Severity-based equipment recommendations that auto-populate based on patient condition
- Enhanced chatbot responses with detailed provider comparisons and pricing information
- Real-time chatbot suggestions when users select different severity levels
- Improved welcome messaging and conversation flow

### Security and Compliance
- HIPAA-compliant data masking in admin panel for sensitive patient information
- Enhanced session data protection with automatic masking of medical/patient fields
- Improved admin interface with refresh functionality and better table styling
- JWT token security with HMAC-SHA256 signing and refresh token management

### Technical Enhancements
- Bootstrap tooltip integration throughout the application
- Smooth scrolling navigation and improved accessibility
- Enhanced JavaScript validation and real-time form interactions
- Improved CSS animations and visual feedback systems

## MediFly Consumer MVP (August 2025)

### Enhanced Consumer MVP Features (Latest Update - August 4, 2025)
Comprehensive update incorporating all advanced features for the Consumer MVP application with focus on user experience, revenue transparency, and operational efficiency.

#### Critical/Non-Critical/MVP Transport Types
- **Landing Page Toggle**: Three-tier transport selection (Critical/Non-Critical/MVP)
- **Critical Transport**: Same-day urgency options with 20% upcharge and weather risk warnings
- **Non-Critical Transport**: Planned transports with family accommodation options
- **MVP Membership**: $49/month program with 10% discounts, priority queue, and beta features
- **Hospital Partnerships**: Institutional pricing and priority matching for bulk bookings

#### Enhanced Equipment & Pricing System
- **Dynamic Equipment Pricing**: Ventilator (+$5K), ECMO (+$10K), Incubator (+$3K), Escort (+$2K), Oxygen (+$1K)
- **Custom Equipment**: "Other" option with text field for specialized medical equipment requests
- **Same-Day Upcharge**: 20% fee for urgent requests with availability warnings
- **Equipment Notifications**: "Provider may recommend additional life-saving equipment" disclaimers

#### AI Command Processing & Address Validation
- **AI Chat Integration**: Natural language transport planning ("help me build a flight for grandma from Orlando to NYC")
- **Google Places API Stub**: Address autocomplete for hospitals, airports, and international destinations
- **Smart Form Filling**: AI commands automatically populate origin/destination and suggest options
- **Command Examples**: Emergency transport, family-friendly options, MVP membership inquiries

#### Provider Competition & Privacy Protection
- **Name Blurring**: Providers shown as "Provider A****", "Provider B****" until booking confirmation
- **Priority Partner Animations**: Gold borders with pulse animations for featured providers
- **Provider Capabilities**: Clear ETA estimates, aircraft type (fixed-wing/helicopter), and certification levels
- **Fair Competition**: Prevents direct contact bypassing to ensure transparent pricing

#### Partnership Integration & Payment Options
- **CareCredit Partnership**: Embedded financing options with low-interest medical payment plans
- **External Payment Links**: No credit card storage, redirects to secure partner payment systems
- **Partnership Exploration**: "Partner with CareCredit for low-interest plans" noted in requirements
- **Security Compliance**: No stored credit card data, session-based temporary information only

#### Enhanced VIP Services & Family Support
- **VIP Cabin Description**: "$10k for luxury pampering with IV treatments, relaxation seats, champagne, priority service"
- **Family Seat Options**: Additional seating based on injury/aircraft with provider confirmation
- **24/7 Family Support**: Dedicated advocate assignment for MVP members
- **Real-Time Updates**: Family communication timeline during transport

#### Partner Dashboard & MOU System
- **Provider Dashboard**: Booking history, revenue tracking, priority status indicators
- **MOU Integration**: Full Memorandum of Understanding with download and email capabilities
- **Priority Partner Benefits**: Enhanced revenue share (90% vs 85%), front-page placement, performance bonuses
- **Revenue Filtering**: Date-based booking filters and performance analytics

#### Cybersecurity & HIPAA Compliance
- **Data Compartmentalization**: Session-based temporary data, automatic purging after 30 days
- **Breach Protection**: Only masked session data visible (e.g., "****-1000" for deposits)
- **No PHI Storage**: Patient information handled securely per HIPAA with temporary session storage
- **Security Indicators**: Visual HIPAA compliance badges and data protection messaging

### Technical Architecture Updates
- **File Structure**: consumer_app_updated.py with enhanced routing and AI integration stubs
- **Enhanced Templates**: Updated consumer_index_updated.html, consumer_intake_updated.html with new features
- **CSS Animations**: Priority partner pulse animations, VIP styling, same-day warning effects
- **Revenue Calculations**: $1,000 deposits + 5% commission structure with transparent breakdowns
- **Port Configuration**: Consumer app on port 5001, Hospital app on port 5000

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templates with a base template system for consistent layout
- **UI Framework**: Bootstrap 5 for responsive design and component styling
- **JavaScript Enhancement**: Custom JavaScript for form navigation, validation, and interactive features
- **Chatbot Integration**: BotUI library integration for conversational interfaces
- **Accessibility**: ARIA labels and semantic HTML for screen reader compatibility

### Backend Architecture
- **Web Framework**: Flask with session-based state management
- **Route Structure**: RESTful routes following a logical user journey (intake → results → confirm → tracking → summary)
- **Data Storage**: Session-based temporary storage with no persistent database
- **Mock Data System**: In-memory provider data simulation for demonstration purposes
- **Logging**: Python logging module for debugging and monitoring

### State Management
- **Session Storage**: Flask sessions for maintaining user data throughout the booking process
- **Temporary Data**: In-memory dictionaries for provider information and tracking stages
- **Security**: Session secret key configuration through environment variables
- **Data Flow**: Linear progression through booking stages with form validation

### Authentication System
- **Admin Access**: Simple credential-based authentication for administrative functions
- **Session Management**: Flask session handling for admin authentication state
- **Security Model**: Basic username/password authentication with demo credentials

## External Dependencies

### Frontend Libraries
- **Bootstrap 5**: CSS framework via CDN for responsive design and components
- **Font Awesome 6**: Icon library via CDN for consistent iconography
- **BotUI**: Chatbot interface library for conversational form interactions

### Backend Dependencies
- **Flask**: Core web framework for routing and request handling
- **Python Standard Library**: datetime, os, logging modules for core functionality

### Environment Configuration
- **SESSION_SECRET**: Environment variable for Flask session security
- **Development Server**: Flask development server with debug mode enabled

### Third-party Integrations
- **CDN Services**: Bootstrap, Font Awesome, and BotUI served via content delivery networks
- **No Database**: Intentionally database-free design for simplicity and demonstration purposes
- **No Email Service**: Mock email notifications logged to console for demonstration