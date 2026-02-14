# Work Journal Maker - Server Synchronization Feature Specification

## Overview

This specification defines the MVP implementation for adding multi-device synchronization capabilities to Work Journal Maker while maintaining zero-knowledge encryption and data portability.

## Core Requirements

### Problem Statement
Users want to synchronize their work logs between multiple devices (computers, phones, tablets) while maintaining security and portability of their data.

### Solution Architecture
- Cloud-hosted synchronization service with zero-knowledge encryption
- Preserve existing local file system structure and functionality
- Integration with existing Work Journal Maker codebase via branching strategy

## Business Model

### Service Tiers
- **Free Trial**: 30-day time-based trial period
- **Paid Subscription**: Unlimited access after trial expires
- **Storage Limit**: 1GB per user account

### Authentication
- Google OAuth for cloud service authentication
- Single authentication method to minimize complexity

## Technical Architecture

### Client-Server Model
- **Deployment**: Cloud-only for MVP (self-hosted options deferred)
- **Integration**: Single codebase with sync features integrated into existing web application
- **Development Strategy**: Feature branch testing before merge to main

### Data Storage and Structure

#### Client-Side Storage
- Maintain existing directory structure:
  ```
  ~/Desktop/worklogs/
  ├── worklogs_2024/
  │   ├── worklogs_2024-04/
  │   │   └── week_ending_2024-04-19/
  │   │       ├── worklog_2024-04-15.txt
  │   │       ├── worklog_2024-04-16.txt
  │   │       └── worklog_2024-04-17.txt
  ```
- Local files remain primary data source
- Users can abandon tool and retain organized data

#### Server-Side Storage
- **Structure**: Flat file organization with metadata
- **Encryption**: All files encrypted at rest using PGP
- **Access**: Zero-knowledge - administrators cannot read user data

### Encryption and Security

#### Zero-Knowledge Architecture
- **Key Generation**: Automatic PGP key pair generation during account setup
- **Key Storage**: Private keys stored locally on user devices
- **Server Storage**: Only public keys and encrypted data stored on server

#### Key Management
- **Primary Method**: QR code sharing between authenticated devices
  - Display encrypted private key as QR code on source device
  - Scan with camera on target device
  - Decrypt locally after password entry
- **Fallback Method**: Manual text file export/import for devices without cameras
- **User Responsibility**: Users warned to backup and secure private keys

#### Key Distribution Security
- **Layered Encryption**: Private key encrypted with random master key, master key encrypted with password-derived key (Argon2)
- **Attack Prevention**: Rate limiting, audit logging, certificate pinning
- **Salt Protection**: Unique salt per user prevents rainbow table attacks

### Synchronization Protocol

#### Sync Timing
- **Method**: Fixed interval synchronization
- **Frequency**: 5-minute intervals
- **Rationale**: Balances data freshness with device resource conservation

#### Conflict Resolution
- **Strategy**: Last writer wins
- **Implementation**: Modification timestamps determine precedence
- **Simplicity**: Avoids complex merge algorithms for MVP

### Data Migration and Import

#### Existing Data Migration
- **Capability**: Users can import existing local journal files to cloud service
- **Frequency**: Ongoing import ability (not just one-time setup)
- **Use Case**: Support for offline work periods (e.g., remote fieldwork)

#### Conflict Handling
- **Method**: User choice for import conflicts
- **Process**: Warn user when local files conflict with existing cloud files
- **Options**: Allow user to choose overwrite, skip, or rename

### Usage Tracking and Billing

#### Account Management
- **Storage Monitoring**: Track data usage against 1GB limit
- **Account Status**: Track paid vs. free trial status
- **Payment Processing**: Payment processor selection deferred (implementation agnostic)

#### Limits and Restrictions
- **Storage**: 1GB maximum per user account
- **Devices**: No device quantity restrictions for MVP

## Implementation Priorities

### MVP Feature Set
1. Google OAuth authentication
2. Zero-knowledge PGP encryption
3. Basic file synchronization with 5-minute intervals
4. QR code key sharing with text file fallback
5. Import functionality for existing local files
6. Usage tracking and account status management
7. 30-day free trial with paid subscription requirement

### Deferred Features
- Self-hosted deployment options
- Multiple authentication providers
- Real-time synchronization
- Advanced conflict resolution
- Custom payment processing integration

## Development Strategy

### Codebase Integration
- **Method**: Create feature branch from existing Work Journal Maker
- **Testing**: Extended testing period on branch before merge
- **Deployment**: Integrated web application with sync capabilities

### Compatibility
- **Backward Compatibility**: Local-only version remains fully functional
- **CLI Tools**: Existing file discovery and CLI tools work unchanged
- **Data Format**: No changes to existing file formats or structure

## Security Considerations

### Data Protection
- **Encryption**: End-to-end encryption using PGP
- **Server Access**: Administrators cannot decrypt user data
- **Key Control**: Users maintain full control of private keys

### Attack Vectors Addressed
- **Server Breach**: Encrypted data remains secure
- **Weak Passwords**: Strong key derivation with Argon2
- **Brute Force**: Rate limiting and account lockouts
- **Man-in-the-Middle**: Certificate pinning

### User Responsibilities
- **Key Backup**: Users responsible for private key security
- **Password Strength**: Strong password requirements
- **Device Security**: Users responsible for device-level security

## Success Metrics

### Technical Metrics
- **Sync Reliability**: >99% successful synchronization events
- **Data Integrity**: Zero data loss incidents
- **Performance**: Sync operations complete within acceptable timeframes

### Business Metrics
- **Trial Conversion**: Track free trial to paid subscription conversion rates
- **User Retention**: Monitor continued usage after subscription
- **Storage Utilization**: Track actual usage against 1GB limits

## Risk Mitigation

### Technical Risks
- **Key Loss**: Clear user education about key backup importance
- **Sync Conflicts**: Simple last-writer-wins reduces complexity
- **Performance**: 5-minute intervals balance freshness with resource usage

### Business Risks
- **Support Overhead**: Focus on cloud-only reduces support complexity
- **Feature Creep**: Strict MVP scope prevents over-engineering
- **Security Vulnerabilities**: Zero-knowledge architecture limits exposure

## Conclusion

This specification defines a focused MVP that adds essential multi-device synchronization to Work Journal Maker while maintaining the application's core principles of data ownership, security, and portability. The implementation strategy balances user needs with development complexity, ensuring a deliverable product that provides immediate value while establishing a foundation for future enhancements.