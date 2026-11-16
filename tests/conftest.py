"""Configuration pytest : variables d'environnement factices avant tout import du projet."""
import os

# Doivent être définies AVANT d'importer common.database / common.security.
os.environ["JWT_SECRET"] = "test-jwt-secret-factice-non-production"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENV"] = "test"
