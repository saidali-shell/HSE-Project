-- Create incidents table
CREATE TABLE incidents (
    incident_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    incident_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    location VARCHAR(255) NOT NULL,
    proof_image_path VARCHAR(500), -- Local path for single incident proof image
    incident_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Reported' CHECK (status IN ('Reported', 'Under Investigation', 'Resolved', 'Closed')),
    reported_by UUID NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for querying incidents by status
CREATE INDEX idx_incidents_status ON incidents(status);
