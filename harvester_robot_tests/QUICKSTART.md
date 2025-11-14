# Quick Start Guide: Running Harvester Robot Framework Tests

This guide will help you quickly set up and run the Harvester Robot Framework tests.

## Step 1: Prerequisites

Ensure you have:
- Python 3.8+ installed
- kubectl installed and configured
- Access to a Harvester cluster
- Kubeconfig file for your Harvester cluster

## Step 2: Install Dependencies

```bash
# Navigate to the test directory
cd tests/harvester_robot_tests

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Configure Environment

```bash
# Copy the example configuration
cp .env.example .env

# Edit the .env file with your cluster details
# Minimum required changes:
# - HARVESTER_ENDPOINT: Your Harvester cluster IP/hostname
# - HARVESTER_USERNAME: Admin username (usually 'admin')
# - HARVESTER_PASSWORD: Your admin password
# - KUBECONFIG: Path to your kubeconfig (optional if using ~/.kube/config)

# Example .env file:
cat > .env << 'EOF'
HARVESTER_ENDPOINT=https://10.115.252.130
HARVESTER_USERNAME=admin
HARVESTER_PASSWORD=mySecurePassword123
KUBECONFIG=/home/user/.kube/config
ROBOT_LOG_LEVEL=INFO
ROBOT_OUTPUT_DIR=./results
EOF
```

## Step 4: Verify Kubernetes Access

```bash
# Test your kubeconfig is working
kubectl get nodes

# You should see your Harvester cluster nodes
# If this fails, check your kubeconfig file path
```

## Step 5: Run Tests

### Quick Test Run

```bash
# Make the run script executable
chmod +x run.sh

# Run all tests
./run.sh

# Or run a specific test
./run.sh -t tests/regression/test_vm.robot
```

### View Results

After tests complete, you'll find results in the output directory (default: `./results/`):

```bash
# Open the HTML report in your browser
open results/report.html  # macOS
xdg-open results/report.html  # Linux
start results/report.html  # Windows

# Or view the detailed log
open results/log.html
```

## Common Commands

```bash
# Run tests with debug logging
./run.sh -L DEBUG -t tests/regression/test_vm.robot

# Run only core tests
./run.sh -i coretest

# Run P0 priority tests only
./run.sh -i p0

# Run all tests except backup tests
./run.sh -e backup

# Show help and all available options
./run.sh -h
```

## Troubleshooting

### Problem: "kubectl: command not found"
**Solution**: Install kubectl from https://kubernetes.io/docs/tasks/tools/

### Problem: "Error: Unable to connect to the server"
**Solution**: 
- Verify your kubeconfig path is correct
- Check that the Harvester cluster is accessible
- Ensure the cluster certificate is valid

### Problem: "Robot Framework not installed"
**Solution**: 
```bash
pip install -r requirements.txt
```

### Problem: Tests fail with "No module named 'kubernetes'"
**Solution**: Make sure you're in the virtual environment:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Problem: ".env file not found" warning
**Solution**: Create the .env file:
```bash
cp .env.example .env
# Edit .env with your settings
```

## Available Test Tags

Use these tags to filter tests:

**Priority Tags:**
- `p0` - Critical priority tests
- `p1` - High priority tests
- `p2` - Medium priority tests

**Type Tags:**
- `coretest` - Core functionality tests
- `regression` - Regression tests
- `smoke` - Smoke tests

**Component Tags:**
- `virtualmachines` - VM tests
- `images` - Image tests
- `volumes` - Volume tests
- `networks` - Network tests
- `backup` - Backup/restore tests

## Example Workflows

### Daily Smoke Test
```bash
./run.sh -i smoke -L INFO
```

### Full Regression Test
```bash
./run.sh -i regression -o ./regression-results
```

### Debug Specific Test
```bash
./run.sh -L DEBUG -t "Test VM Basic Lifecycle"
```

### Run Core Tests Only
```bash
./run.sh -i coretest -i p0
```

## Next Steps

- Read the full [README.md](README.md) for detailed architecture information
- Check [tests/](tests/) directory for available test suites
- Learn about writing new tests in the main README

## Support

For issues or questions:
- Check the main README.md file
- Review test logs in the results directory
- Check Harvester documentation: https://docs.harvesterhci.io/
