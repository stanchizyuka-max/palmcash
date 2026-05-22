-- SQL script to add audit timestamp columns to loans_loan table
-- Run this on the production database if migration fails

-- Add approval_recorded_at column
ALTER TABLE loans_loan 
ADD COLUMN approval_recorded_at DATETIME(6) NULL 
COMMENT 'System timestamp: when approval was recorded in the system';

-- Add disbursement_recorded_at column
ALTER TABLE loans_loan 
ADD COLUMN disbursement_recorded_at DATETIME(6) NULL 
COMMENT 'System timestamp: when disbursement was recorded in the system';

-- Verify columns were added
DESCRIBE loans_loan;
