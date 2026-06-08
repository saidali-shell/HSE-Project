-- Create approvals table
CREATE TABLE approvals (
    approval_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    module_type VARCHAR(20) NOT NULL CHECK (module_type IN ('TASK', 'TRAINING')),
    reference_id UUID NOT NULL, -- UUID referencing training_id, or task_id
    requested_by UUID NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    approved_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Approved', 'Rejected')),
    comments TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for searching approvals
CREATE INDEX idx_approvals_status ON approvals(status);
CREATE INDEX idx_approvals_requested_by ON approvals(requested_by);
CREATE INDEX idx_approvals_reference ON approvals(module_type, reference_id);
