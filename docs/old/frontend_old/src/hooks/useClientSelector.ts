import { useSelector } from 'react-redux';
import { RootState } from '../app/store';

export const useClientSelector = () => {
  const selectedClient = useSelector((state: RootState) => state.client.selectedClient);
  const clientList = useSelector((state: RootState) => state.client.clientList);

  return {
    selectedClient,
    clientList,
  };
};