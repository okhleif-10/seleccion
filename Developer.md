# For Developers

In your terminal:

1. Clone `seleccion`
 ```
git clone https://github.com/okhleif-10/seleccion.git
cd seleccion
 ```
2. Install dependencies
```
virtualenv -p python3 seleccion_env
source seleccion_env/bin/activate
pip install -r requirements.txt
```
3. Run app.py locally
```
streamlit run app.py
```
4. Run tests
```
# Configure `main()` in test.py to your liking. By default, full workflow for all 211 teams will be tested
python test.py
```

# Issues / Bugs

To report any bugs, please open an issue, or optionally, submit a PR for review. All PR's require one approval from the Codeowner.
