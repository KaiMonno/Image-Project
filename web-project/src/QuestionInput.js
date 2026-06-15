import React, { useEffect, useState } from 'react';
import uploadImage from './ImageService';
import tasteCatalog, { categoryOrder } from './tasteCatalog';
import { API_BASE_URL } from './config';

function QuestionInput() {
  const [catalog, setCatalog] = useState(tasteCatalog);
  const [isCatalogLoading, setIsCatalogLoading] = useState(true);
  const [catalogError, setCatalogError] = useState('');
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedOption, setSelectedOption] = useState(null);
  const [selections, setSelections] = useState({});
  const [finalImageUrl, setFinalImageUrl] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [userId] = useState(() => `user_${Date.now()}_${Math.random().toString(36).slice(2)}`);

  const currentCategory = categoryOrder[currentStep];
  const currentCategoryDetails = catalog[currentCategory];
  const isComplete = Boolean(finalImageUrl);

  useEffect(() => {
    let isMounted = true;

    fetch(`${API_BASE_URL}/api/catalog`)
      .then((response) => {
        if (!response.ok) {
          throw new Error('Could not load the catalog.');
        }

        return response.json();
      })
      .then((catalogFromDatabase) => {
        if (isMounted) {
          setCatalog(catalogFromDatabase);
          setCatalogError('');
        }
      })
      .catch((loadError) => {
        if (isMounted) {
          setCatalogError(loadError.message || 'Using local fallback catalog.');
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsCatalogLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const handleOptionClick = (option) => {
    setSelectedOption(option);
    setError('');
  };

  const handleConfirm = async () => {
    if (!selectedOption || isUploading) {
      return;
    }

    setIsUploading(true);
    setError('');

    try {
      const imageResponse = await fetch(selectedOption.imageUrl);
      if (!imageResponse.ok) {
        throw new Error('Could not load the selected image.');
      }

      const imageBlob = await imageResponse.blob();
      const imageFile = new File([imageBlob], `${selectedOption.id}.png`, { type: imageBlob.type });
      const result = await uploadImage(imageFile, currentCategory, userId);

      setSelections((currentSelections) => ({
        ...currentSelections,
        [currentCategory]: selectedOption,
      }));

      if (result.status === 'complete') {
        setFinalImageUrl(result.imageUrl);
      } else {
        setCurrentStep((step) => step + 1);
        setSelectedOption(null);
      }
    } catch (uploadError) {
      setError(uploadError.message || 'Something went wrong while saving your pick.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <main className="taste-builder">
      <section className="builder-panel">
        <p className="eyebrow">Taste Collage</p>
        <h1>Build a snapshot of your taste.</h1>
        <p className="intro">
          Choose one artist, movie, and show. The app combines your picks into a single shareable image.
        </p>

        <div className="step-list" aria-label="Progress">
          {categoryOrder.map((category, index) => (
            <div
              className={`step-pill ${index === currentStep ? 'active' : ''} ${selections[category] ? 'done' : ''}`}
              key={category}
            >
              {catalog[category].label}
            </div>
          ))}
        </div>

        {isCatalogLoading ? (
          <p className="status-message">Loading options from the image database...</p>
        ) : !isComplete ? (
          <>
            {catalogError && <p className="status-message">{catalogError}</p>}
            <div className="question-header">
              <span>Step {currentStep + 1} of {categoryOrder.length}</span>
              <h2>{currentCategoryDetails.prompt}</h2>
            </div>

            <div className="option-grid">
              {currentCategoryDetails.options.map((option) => (
                <button
                  className={`option-card ${selectedOption?.id === option.id ? 'selected' : ''}`}
                  key={option.id}
                  onClick={() => handleOptionClick(option)}
                  type="button"
                >
                  <img src={option.imageUrl} alt="" />
                  <strong>{option.name}</strong>
                  <span>{option.description}</span>
                </button>
              ))}
            </div>

            {error && <p className="error-message">{error}</p>}

            <button
              className="primary-action"
              disabled={!selectedOption || isUploading}
              onClick={handleConfirm}
              type="button"
            >
              {isUploading ? 'Saving pick...' : `Confirm ${currentCategoryDetails.label}`}
            </button>
          </>
        ) : (
          <div className="result-panel">
            <h2>Your taste image is ready.</h2>
            <img src={finalImageUrl} alt="Combined taste collage" />
            <div className="selection-summary">
              {categoryOrder.map((category) => (
                <p key={category}>
                  <strong>{catalog[category].label}:</strong> {selections[category]?.name}
                </p>
              ))}
            </div>
          </div>
        )}
      </section>
    </main>
  );
}


export default QuestionInput;
