# MediFly Hospital MVP

## Overview

MediFly is a Flask-based web application that simulates a hospital interface for booking air medical transport services. The system provides a streamlined workflow for hospital staff to coordinate critical patient transports, from initial intake through flight tracking and completion. The application features a multi-step guided form, enhanced provider comparison with visual capability badges, booking confirmation, real-time flight tracking simulation with improved animations, intelligent chatbot assistance with severity-based recommendations, and administrative oversight capabilities with HIPAA-compliant data masking.

## Recent Enhancements (August 2025)

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

### Overview
Created a separate Flask web application called "MediFly Consumer MVP" tailored specifically for families and individuals seeking medical transport for their loved ones. This family-focused version uses empathetic language, pastel styling, and provides a more personal, compassionate interface compared to the clinical Hospital MVP.

### Key Features
- **Family-Focused Design**: Empathetic language throughout ("Get Your Loved One Home Safely", "We're With You Every Step")
- **Toggle Interface**: Landing page toggle between "Family/Individual" (default) vs "Hospital/Insurance" modes
- **Animated Header**: CSS keyframes helicopter flying left-to-right, transitioning to plane circling globe animation
- **Pastel Theme**: Soft blues (#e6f3ff), pinks (#ffe6f3), and warm whites with rounded corners and gentle shadows
- **Enhanced UX**: Larger touch targets, family-friendly messaging, and simplified navigation flow

### Consumer App Architecture
- **File Structure**: Separate templates (consumer_templates/), static files (consumer_static/), and consumer_app.py
- **Pastel Styling**: Custom CSS with variables for consistent pastel color scheme and smooth animations
- **Family Chatbot**: Context-aware chatbot providing family-specific guidance and support
- **HIPAA Compliance**: Session-based data handling with automatic masking of sensitive information
- **Accessibility**: ARIA labels, semantic HTML, and screen reader compatibility throughout

### Consumer-Specific Features
- **Family Accommodations**: Family Seat option (+$5,000) and VIP Cabin upgrade (+$10,000)
- **Compassionate Messaging**: "Ready to help your family", "We prioritize your family's peace of mind"
- **Enhanced Tracking**: Family update timeline with regular communication during transport
- **Support Integration**: 24/7 family support line with dedicated reference numbers
- **Privacy Assurance**: Clear messaging about temporary data use and automatic session clearing

### Deployment Configuration
- **Separate App**: consumer_app.py runs independently from hospital app
- **Port Configuration**: Consumer app runs on port 5001, Hospital app remains on port 5000
- **Environment Toggling**: Can be deployed separately or with toggle functionality
- **URL Structure**: Designed for medtransportlink-consumer.replit.app deployment

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