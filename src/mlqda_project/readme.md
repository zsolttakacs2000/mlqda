# README
## Deploy MLQDA locally

### Steps to setup your environment
1. Install Anaconda as suggested by their [website](https://docs.anaconda.com/anaconda/install/).
2. Open Anaconda Powershell Prompt
3. Create a virtual environment with python 3.9 using the following command.
    ```
    conda create -n <your-environment-name> python=3.9
    ```
    Answer yes (y) when prompted to download base packages.
4. Activate your virtual environment with the following command
    ```
    conda activate <your-environment-name>
    ```
5. Clone this project by running the following command
    ```
    git clone https://github.com/zsolttakacs2000/mlqda.git
    ```
6. Navigate to the source folder, the same level where `manage.py` or `requiremnets.txt` is located. You can sue the following command if you just cloned the project
    ```
    cd mlqda/src/mlqda_project
    ```
7. Install requirements with the follwoing command
    ```
    pip install -r requirements.txt
    ```

### Steps to deploy the project locally
Once you have you environment set up you can use the following commands to launch a local server instance on your machine.
1. Make migrations
    ```
    python manage.py makemigrations
    ```
2. Migrate
    ```
    python manage.py migrate
    ```
3. Launch server
    ```
    python manage.py runserver
    ```
4. Open site
    The site is usually available at the following address while server is running on your terminal.
    http://127.0.0.1:8000/
    Please double check this address in your console window.

### Test the implementation
1. Run the test using the following command
    ```
    coverage run --source='.' manage.py test mlqda
    ```
2. Check coverage
    ```
    coverage report -m
    ```