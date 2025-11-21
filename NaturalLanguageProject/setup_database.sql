-- setup_database.sql

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Drop tables if they exist (to reset everything)
DROP TABLE IF EXISTS PersonToLab;
DROP TABLE IF EXISTS Room;
DROP TABLE IF EXISTS Student;
DROP TABLE IF EXISTS Person;
DROP TABLE IF EXISTS Lab;
DROP TABLE IF EXISTS Department;
DROP TABLE IF EXISTS Building;

-- Create tables
CREATE TABLE Department (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE Lab (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    departmentID INTEGER,
    FOREIGN KEY(departmentID) REFERENCES Department(id)
);

CREATE TABLE Person (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    firstName TEXT NOT NULL,
    lastName TEXT NOT NULL,
    departmentID INTEGER,
    areaOfResearch TEXT,
    personType TEXT CHECK(personType IN ('professor','undergraduateStudent','graduateStudent','faculty')),
    FOREIGN KEY(departmentID) REFERENCES Department(id)
);

CREATE TABLE Building (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    constructionCompleted Date NOT NULL,
    floorCount INTEGER
);

CREATE TABLE Room (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    buildingID INTEGER,
    labID INTEGER,
    roomNumber TEXT,
    FOREIGN KEY(buildingID) REFERENCES Building(id),
    FOREIGN KEY(labID) REFERENCES Lab(id)
);

CREATE TABLE PersonToLab (
    personID INTEGER,
    labID INTEGER,
    FOREIGN KEY(personID) REFERENCES Person(id),
    FOREIGN KEY(labID) REFERENCES Lab(id),
    PRIMARY KEY(personID, labID)
);

-- ============================================
-- INSERT DATA
-- ============================================

-- Departments
INSERT INTO Department (name) VALUES 
    ('Computer Science'), 
    ('Chemistry'), 
    ('Physics'), 
    ('ACME'), 
    ('Math'), 
    ('Mechanical Engineering'), 
    ('Electrical Engineering'), 
    ('Computer Engineering'), 
    ('Civil Engineering'), 
    ('Statistics');

-- Labs
INSERT INTO Lab (name, departmentID) VALUES 
    -- Computer Science
    ('Internet Security Research Lab', 1), 
    ('IDeA Labs', 1),
    ('DRAGN Labs', 1),
    ('Advanced 3D Computer Graphics Lab', 1),
    ('Family History Technology Lab', 1),
    ('Bio Lab', 2),
    ('Computational Creativity and Control Lab', 1),
    ('Machine Intelligence and Discovery Lab', 1),
    ('Human-Centered Machine Intelligence Lab', 1),
    ('Mobile Computing Lab', 1),
    ('Data Mining Lab', 1),
    ('Computer Vision and Perception Lab', 1),

    -- Mechanical Engineering
    ('Flow Physics and Simulation Lab', 6),
    ('Robotics and Dynamics Lab', 6),
    ('Compliant Mechanisms Research Lab', 6),
    ('Thermal Fluids Research Lab', 6),
    ('Additive Manufacturing Lab', 6);

-- People
INSERT INTO Person (firstName, lastName, departmentID, areaOfResearch, personType) VALUES 
    -- Computer Science professors (original + new)
    ('Parris','Egbert', 1, 'Interactive 3D graphics and virtual environments', 'professor'),
    ('Casey','Deccio', 1, 'Network measurement and anti-abuse for Internet stability and security', 'professor'),
    ('Kent','Seamons', 1, '', 'professor'),
    ('Nancy','Fulda', 1, '', 'professor'),
    ('Quinn','Snell', 1, 'High-performance computing and bioinformatics', 'professor'),
    ('Mark','Clement', 1, 'Computational biology and genealogy technology', 'professor'),
    ('Michael','Jones', 1, 'Computer vision and 3D reconstruction', 'professor'),
    ('Dan','Ventura', 1, 'Artificial intelligence and computational creativity', 'professor'),
    ('Charles','Knutson', 1, 'Software engineering and mobile computing', 'professor'),
    ('Dennis','Ng', 1, 'Human-computer interaction and educational technologies', 'professor'),

    -- Mechanical Engineering professors
    ('Spencer','Magleby', 6, 'Compliant mechanisms and product design', 'professor'),
    ('Brian','Iverson', 6, 'Heat transfer and energy systems', 'professor'),
    ('David','Fullwood', 6, 'Micromechanics and materials science', 'professor'),
    ('Andrew','Merryweather', 6, 'Biomechanics and human safety', 'professor'),
    ('Scott','Thomson', 6, 'Aeroacoustics and fluid mechanics', 'professor'),
    ('Jeremy','Lee', 6, 'Robotics, control, and dynamic systems', 'professor'),

    -- Students
    ('Bob', '', 2, 'Genetics', 'graduateStudent'),
    ('Alice','Johnson', 1, 'Machine learning applications in cybersecurity', 'graduateStudent'),
    ('Ethan','Park', 1, '3D rendering optimization', 'undergraduateStudent'),
    ('Sofia','Reyes', 1, 'Human-centered computing', 'graduateStudent'),
    ('Liam','Chen', 6, 'Additive manufacturing techniques', 'graduateStudent'),
    ('Noah','Miller', 6, 'Robotics kinematics', 'undergraduateStudent'),
    ('Grace','Lee', 6, 'Thermal analysis in fluid systems', 'graduateStudent');

-- Buildings
INSERT INTO Building (name, constructionCompleted, floorCount) VALUES
    ('Talmage Building (TMCB)', '1971-09-01', 6),        -- Computer Science
    ('Engineering Building (EB)', '2018-09-04', 5),       -- Mechanical & Civil Engineering
    ('Life Sciences Building (LSB)', '2014-09-01', 5),    -- Biology & Chemistry
    ('Hinckley Center', '2007-08-01', 3),                 -- Admin & faculty offices
    ('Cluff Building', '1950-01-01', 3);                  -- Older engineering facility

-- Rooms
INSERT INTO Room (buildingID, labID, roomNumber) VALUES
    -- TMCB - Computer Science labs
    (1, 1, 'TMCB 1170'),  -- Internet Security Research Lab
    (1, 2, 'TMCB 1111'),  -- IDeA Labs
    (1, 3, 'TMCB 1122'),  -- DRAGN Labs
    (1, 4, 'TMCB 1174'),  -- Advanced 3D Computer Graphics Lab
    (1, 5, 'TMCB 1172'),  -- Family History Technology Lab
    (1, 7, 'TMCB 1180'),  -- Computational Creativity and Control Lab
    (1, 9, 'TMCB 1182'),  -- Human-Centered Machine Intelligence Lab
    (1, 10, 'TMCB 1190'), -- Mobile Computing Lab
    (1, 12, 'TMCB 1158'), -- Computer Vision and Perception Lab

    -- EB - Mechanical Engineering labs
    (2, 13, 'EB 310'),  -- Flow Physics and Simulation Lab
    (2, 14, 'EB 215'),  -- Robotics and Dynamics Lab
    (2, 15, 'EB 375'),  -- Compliant Mechanisms Research Lab
    (2, 16, 'EB 230'),  -- Thermal Fluids Research Lab
    (2, 17, 'EB 250'),  -- Additive Manufacturing Lab

    -- LSB - Bio Lab (Chemistry department)
    (3, 6, 'LSB 4100');

-- Person to Lab relationships
INSERT INTO PersonToLab (personID, labID) VALUES 
    -- Computer Science professors
    (1, 4),   -- Parris Egbert -> Advanced 3D Computer Graphics Lab
    (2, 1),   -- Casey Deccio -> Internet Security Research Lab
    (3, 1),   -- Kent Seamons -> Internet Security Research Lab
    (4, 3),   -- Nancy Fulda -> DRAGN Labs
    (5, 7),   -- Quinn Snell -> Computational Creativity and Control Lab
    (6, 5),   -- Mark Clement -> Family History Technology Lab
    (7, 12),  -- Michael Jones -> Computer Vision and Perception Lab
    (8, 7),   -- Dan Ventura -> Computational Creativity and Control Lab
    (9, 10),  -- Charles Knutson -> Mobile Computing Lab
    (10, 9),  -- Dennis Ng -> Human-Centered Machine Intelligence Lab

    -- Mechanical Engineering professors
    (11, 15), -- Spencer Magleby -> Compliant Mechanisms Research Lab
    (12, 16), -- Brian Iverson -> Thermal Fluids Research Lab
    (13, 17), -- David Fullwood -> Additive Manufacturing Lab
    (14, 14), -- Andrew Merryweather -> Robotics and Dynamics Lab
    (15, 13), -- Scott Thomson -> Flow Physics and Simulation Lab
    (16, 14), -- Jeremy Lee -> Robotics and Dynamics Lab

    -- Students
    (17, 1),  -- Bob -> Bio Lab (Chemistry)
    (18, 1),  -- Alice Johnson -> Internet Security Research Lab
    (19, 4),  -- Ethan Park -> Advanced 3D Computer Graphics Lab
    (20, 9),  -- Sofia Reyes -> Human-Centered Machine Intelligence Lab
    (21, 17), -- Liam Chen -> Additive Manufacturing Lab
    (22, 14), -- Noah Miller -> Robotics and Dynamics Lab
    (23, 17); -- Grace Lee -> Thermal Fluids Research Lab
