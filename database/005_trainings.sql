-- Create trainings table
CREATE TABLE trainings (
    training_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID REFERENCES incidents(incident_id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    training_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    instructor VARCHAR(255) NOT NULL,
    assigned_to UUID NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    status VARCHAR(20) NOT NULL DEFAULT 'Assigned' CHECK (status IN ('Assigned', 'In Progress', 'Completed')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_by UUID NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for searching trainings by status or assignee
CREATE INDEX idx_trainings_assigned_to ON trainings(assigned_to);
CREATE INDEX idx_trainings_status ON trainings(status);
CREATE INDEX idx_trainings_incident_id ON trainings(incident_id);
